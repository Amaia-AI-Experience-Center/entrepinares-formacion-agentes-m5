"""Pruebas OFFLINE del adaptador, del cliente Hosted y de la estructura de los cuadernos.

No usan red, ni Azure, ni Foundry, ni credenciales. Ejecutar desde la raiz:

    python -B -m unittest discover -s notebooks/tests -v
"""

import ast
import asyncio
import importlib.util
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

NOTEBOOKS = Path(__file__).resolve().parents[1]
RAIZ = NOTEBOOKS.parent
sys.path.insert(0, str(NOTEBOOKS))

import entrepinares_utils as u  # noqa: E402

try:
    import nbformat
except ImportError:  # pragma: no cover
    nbformat = None

NB1 = NOTEBOOKS / "entrepinares_01_fundamentos_offline.ipynb"
NB2 = NOTEBOOKS / "entrepinares_02_workflow_foundry.ipynb"


class AdaptadorTest(unittest.TestCase):
    def test_preparar_entorno_bloquea_descargas_cisa(self):
        u.preparar_entorno(cargar_env=False)
        import fuente_kev

        with self.assertRaises(RuntimeError):
            fuente_kev.descargar_catalogo()

    def test_huellas_y_comparacion(self):
        with tempfile.TemporaryDirectory() as t:
            carpeta = Path(t)
            (carpeta / "a.txt").write_text("uno")
            (carpeta / "sub").mkdir()
            (carpeta / "sub" / "b.txt").write_text("dos")
            antes = u.huellas_datos(carpeta)
            self.assertEqual(set(antes), {"a.txt", "sub/b.txt"})
            self.assertFalse(any(u.comparar_huellas(antes, u.huellas_datos(carpeta)).values()))
            (carpeta / "a.txt").write_text("cambiado")
            (carpeta / "c.txt").write_text("nuevo")
            (carpeta / "sub" / "b.txt").unlink()
            dif = u.comparar_huellas(antes, u.huellas_datos(carpeta))
            self.assertEqual(dif, {"modificados": ["a.txt"], "nuevos": ["c.txt"], "ausentes": ["sub/b.txt"]})

    def test_huellas_de_datos_reales_incluyen_inventario(self):
        self.assertIn("inventario_demo.csv", u.huellas_datos())

    def test_configuracion_sin_y_con_endpoint(self):
        with patch.dict(os.environ, {}, clear=True):
            c = u.comprobar_configuracion()
            self.assertFalse(c["endpoint_configurado"])
            self.assertIsNone(c["host_endpoint"])
            self.assertEqual(c["modelo"], "gpt-4.1-mini")
            self.assertFalse(c["tenant_indicado"])
        with patch.dict(os.environ, {"FOUNDRY_PROJECT_ENDPOINT": "https://x.services.ai.azure.com/api/projects/p",
                                     "AZURE_TENANT_ID": "t"}, clear=True):
            c = u.comprobar_configuracion()
            self.assertTrue(c["endpoint_configurado"])
            self.assertEqual(c["host_endpoint"], "x.services.ai.azure.com")
            self.assertTrue(c["tenant_indicado"])

    def test_crear_cliente_sin_endpoint_falla_con_mensaje_claro(self):
        m = u.preparar_entorno(cargar_env=False)
        with patch.dict(os.environ, {"FOUNDRY_PROJECT_ENDPOINT": ""}):
            with patch.object(m, "PROJECT_ENDPOINT", ""):
                with self.assertRaisesRegex(RuntimeError, "FOUNDRY_PROJECT_ENDPOINT"):
                    m.crear_cliente()

    def test_cliente_usa_azure_cli_y_el_tenant_opcional(self):
        m = u.preparar_entorno(cargar_env=False)
        self.assertFalse(hasattr(m, "ClientSecretCredential"), "no debe quedar autenticacion por aplicacion")
        entorno = {"FOUNDRY_PROJECT_ENDPOINT": "https://ejemplo.invalid/api/projects/p"}
        with patch.dict(os.environ, entorno, clear=True):
            with patch.object(m, "AzureCliCredential") as cli, patch.object(m, "FoundryChatClient") as cliente:
                m.crear_cliente()
            cli.assert_called_once_with()
            self.assertEqual(cliente.call_args.kwargs["model"], "gpt-4.1-mini")
        with patch.dict(os.environ, {**entorno, "AZURE_TENANT_ID": "mi-tenant"}, clear=True):
            with patch.object(m, "AzureCliCredential") as cli, patch.object(m, "FoundryChatClient"):
                m.crear_cliente()
            cli.assert_called_once_with(tenant_id="mi-tenant")

    def test_workflow_sin_conexion_es_de_solo_lectura(self):
        m = u.preparar_entorno(cargar_env=False)
        workflow, agentes = u.construir_workflow_sin_conexion(m)
        self.assertEqual(set(agentes), {"AgenteOrquestador", "AgenteCorrelacion", "AgenteCriticidad"})
        nombres = set()
        for agente in agentes.values():
            nombres |= {t.name for t in agente.default_options.get("tools", [])}
        self.assertNotIn("actualizar_novedades_cisa_controlada", nombres)
        self.assertNotIn("generar_informes_controlados", nombres)
        self.assertIn("consultar_cribado", nombres)
        mermaid = u.diagrama_mermaid(workflow)
        for nodo in ("AgenteOrquestador", "AgenteCorrelacion", "AgenteCriticidad", "RespuestaFinal"):
            self.assertIn(nodo, mermaid)

    def test_informe_local_va_a_otra_carpeta_y_no_toca_datos_ni_informes(self):
        u.preparar_entorno(cargar_env=False)
        import generar_html
        import generar_informe

        rutas_originales = (generar_informe.RUTA_INFORME, generar_html.ORIGEN, generar_html.DESTINO)
        antes = u.huellas_datos()
        informes_antes = sorted((RAIZ / "informes").glob("*")) if (RAIZ / "informes").exists() else []
        with tempfile.TemporaryDirectory() as t:
            r = u.generar_informe_local(Path(t))
            self.assertTrue(r["markdown"].is_file() and r["html"].is_file())
            self.assertIn("IT-", r["markdown"].read_text(encoding="utf-8"))
            self.assertIn("<html", r["html"].read_text(encoding="utf-8").lower())
        self.assertEqual(rutas_originales, (generar_informe.RUTA_INFORME, generar_html.ORIGEN, generar_html.DESTINO))
        self.assertFalse(any(u.comparar_huellas(antes, u.huellas_datos()).values()))
        informes_despues = sorted((RAIZ / "informes").glob("*")) if (RAIZ / "informes").exists() else []
        self.assertEqual(informes_antes, informes_despues)

    def test_evidencias_datos(self):
        e = u.evidencias_datos()
        self.assertRegex(e["catalogo_cisa"]["version"], r"^\d{4}\.\d{2}\.\d{2}$")
        self.assertGreater(e["catalogo_cisa"]["total_cve"], 1000)
        self.assertIn("resumen", e["cribado"])

    def test_traza_con_eventos_sinteticos(self):
        from agent_framework import AgentResponse, Content, Message
        from agent_framework._workflows._events import WorkflowEvent

        decision = {
            "ruta": "correlacion", "asset_id": "IT-004", "cve_id": None,
            "accion_explicita": "ninguna", "respuesta_directa": None, "motivo": "prueba",
        }
        resp_orq = AgentResponse(messages=[Message(role="assistant", contents=[json.dumps(decision)])])
        resp_corr = AgentResponse(messages=[
            Message(role="assistant", contents=[
                Content.from_function_call("c1", "consultar_cribado", arguments='{"asset_id": "IT-004"}')]),
            Message(role="tool", contents=[Content.from_function_result("c1", result='{"ok": true}')]),
            Message(role="assistant", contents=["Resumen de candidatas."]),
        ])
        eventos = [
            WorkflowEvent("executor_invoked", executor_id="AgenteOrquestador"),
            WorkflowEvent("intermediate", resp_orq, executor_id="AgenteOrquestador"),
            WorkflowEvent("executor_invoked", executor_id="AgenteCorrelacion"),
            WorkflowEvent("intermediate", resp_corr, executor_id="AgenteCorrelacion"),
            WorkflowEvent("executor_invoked", executor_id="RespuestaFinal"),
        ]

        class Resultado(list):
            def get_outputs(self):
                return ["Respuesta final de prueba"]

            def get_request_info_events(self):
                return []

        class FalsoWorkflow:
            async def run(self, pregunta):
                return Resultado(eventos)

        t = asyncio.run(u.ejecutar_consulta("¿Candidatas IT-004?", workflow=FalsoWorkflow()))
        self.assertEqual(t.ruta, ["AgenteOrquestador", "AgenteCorrelacion", "RespuestaFinal"])
        self.assertEqual(t.agentes, ["AgenteOrquestador", "AgenteCorrelacion"])
        self.assertEqual(t.decision["ruta"], "correlacion")
        self.assertEqual([h.nombre for h in t.herramientas], ["consultar_cribado"])
        self.assertIn("IT-004", t.herramientas[0].argumentos)
        self.assertEqual(t.herramientas[0].resultado, '{"ok": true}')
        self.assertEqual(t.respuesta, "Respuesta final de prueba")

    def test_explicar_error_sin_secretos(self):
        self.assertIn("az login", u.explicar_error(RuntimeError("Please run 'az login' to set up an account")))
        self.assertIn(".env", u.explicar_error(RuntimeError("Falta FOUNDRY_PROJECT_ENDPOINT")))
        self.assertIn("rol", u.explicar_error(RuntimeError("Error code: 403 PermissionDenied")))
        self.assertIn("tenant", u.explicar_error(RuntimeError("AADSTS90002: Tenant not found")))
        texto = u.explicar_error(RuntimeError("fallo https://x/y?sv=2026&sig=ABCDEFGHIJKLMNOP token eyJabcdefghijklmnopqrstuvwxyz.abc"))
        self.assertNotIn("ABCDEFGHIJKLMNOP", texto)
        self.assertNotIn("eyJabcdefghijklmnopqrstuvwxyz", texto)


def _cargar_cliente_hosted():
    spec = importlib.util.spec_from_file_location("probar_hosted_v5", RAIZ / "scripts" / "probar_hosted_v5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ClienteHostedTest(unittest.TestCase):
    def test_no_aprueba_ni_imprime_secretos(self):
        h = _cargar_cliente_hosted()
        self.assertEqual(h._ocultar("u?sv=1&sig=SECRETO123&se=2026"), "u?sv=***&sig=***&se=***")
        fuente = (RAIZ / "scripts" / "probar_hosted_v5.py").read_text(encoding="utf-8")
        self.assertNotIn("approve=True", fuente)
        self.assertNotIn("approved=True", fuente)
        self.assertNotIn("to_function_approval_response", fuente)

    def test_detecta_negativas_aunque_la_respuesta_repita_la_pregunta(self):
        h = _cargar_cliente_hosted()
        caso = h.PRUEBAS["correlacion"]
        mala = "No se pudo realizar el cribado para la CVE-2026-124194: el KEV activo no está disponible en el Blob."
        self.assertFalse(h.evaluar(mala, caso)[0])
        buena = "Sí: el cribado de IT-007 incluye CVE-2026-124194 (coincidencia solo por fabricante)."
        self.assertTrue(h.evaluar(buena, caso)[0])


def _fuentes(ruta):
    nb = nbformat.read(ruta, as_version=4)
    return nb, [c for c in nb.cells if c.cell_type == "code"]


@unittest.skipIf(nbformat is None, "nbformat no instalado")
class CuadernosTest(unittest.TestCase):
    def test_los_cuadernos_existen_y_estan_limpios(self):
        for ruta in (NB1, NB2):
            self.assertTrue(ruta.is_file(), ruta)
            nb, codigo = _fuentes(ruta)
            nbformat.validate(nb)
            for c in codigo:
                self.assertEqual(c.outputs, [], f"{ruta.name}: celda con salida guardada")
                self.assertIsNone(c.execution_count)

    def test_todas_las_celdas_compilan(self):
        flags = ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        for ruta in (NB1, NB2):
            _, codigo = _fuentes(ruta)
            for i, c in enumerate(codigo):
                fuente = "\n".join(l for l in c.source.splitlines() if not l.lstrip().startswith(("%", "!")))
                compile(fuente, f"{ruta.name}#{i}", "exec", flags)

    def test_sin_secretos_ni_endpoints_reales(self):
        patron = re.compile(r"sig=|sv=20|AccountKey|PRIVATE KEY|eyJ[A-Za-z0-9_-]{20,}|services\.ai\.azure\.com/api/projects/[a-z]")
        for ruta in (NB1, NB2):
            self.assertIsNone(patron.search(ruta.read_text(encoding="utf-8")), ruta.name)

    def test_cuaderno1_bloquea_descargas_antes_de_usar_herramientas(self):
        _, codigo = _fuentes(NB1)
        fuentes = [c.source for c in codigo]
        i_prep = next(i for i, s in enumerate(fuentes) if "preparar_entorno" in s)
        usan = [i for i, s in enumerate(fuentes) if ".func(" in s or "generar_informe_local" in s]
        self.assertTrue(usan)
        self.assertTrue(all(i > i_prep for i in usan))

    def test_cuaderno2_es_de_solo_lectura(self):
        texto = NB2.read_text(encoding="utf-8")
        self.assertNotIn("acciones_interactivas=True", texto)
        self.assertNotIn("permitir_escrituras=True", texto)
        self.assertNotIn("permitir_informes=True", texto)

    def test_cuaderno2_importa_el_adaptador(self):
        _, codigo = _fuentes(NB2)
        self.assertTrue(any("entrepinares_utils" in c.source for c in codigo))


class RepositorioTest(unittest.TestCase):
    def test_sin_codespaces_ni_autenticacion_por_aplicacion(self):
        self.assertFalse((RAIZ / ".devcontainer").exists())
        self.assertFalse((RAIZ / "requirements-codespaces.lock.txt").exists())
        for ruta in list(RAIZ.glob("*.py")) + list((RAIZ / "scripts").glob("*")) + [NOTEBOOKS / "entrepinares_utils.py"]:
            texto = ruta.read_text(encoding="utf-8")
            self.assertNotIn("ClientSecretCredential", texto, ruta.name)
            self.assertNotIn("AZURE_CLIENT_SECRET", texto, ruta.name)

    def test_gitignore_protege_secretos_y_salidas(self):
        texto = (RAIZ / ".gitignore").read_text(encoding="utf-8")
        for patron in (".env", ".venv/", "salidas/", "informes/", "*.log"):
            self.assertIn(patron, texto)


if __name__ == "__main__":
    unittest.main()
