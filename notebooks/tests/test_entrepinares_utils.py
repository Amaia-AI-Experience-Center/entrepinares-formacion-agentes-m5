"""Pruebas OFFLINE del adaptador y de la estructura de los cuadernos.

No usan red, ni Azure, ni Foundry, ni credenciales. Ejecutar desde la raiz:

    python -B -m unittest discover -s notebooks/tests -v
"""

import ast
import asyncio
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
            self.assertFalse(c["autenticacion_completa"])
            self.assertEqual(c["autenticacion"], {n: False for n in u.VARIABLES_AUTENTICACION})
        with patch.dict(os.environ, {"FOUNDRY_PROJECT_ENDPOINT": "https://x.services.ai.azure.com/api/projects/p"}, clear=True):
            c = u.comprobar_configuracion()
            self.assertTrue(c["endpoint_configurado"])
            self.assertEqual(c["host_endpoint"], "x.services.ai.azure.com")

    def test_configuracion_nunca_expone_valores_secretos(self):
        secreto = "SECRETO-DE-PRUEBA-1234567890"
        entorno = {"AZURE_TENANT_ID": "t-prueba", "AZURE_CLIENT_ID": "c-prueba", "AZURE_CLIENT_SECRET": secreto}
        with patch.dict(os.environ, entorno, clear=True):
            c = u.comprobar_configuracion()
        self.assertTrue(c["autenticacion_completa"])
        self.assertNotIn(secreto, json.dumps(c))
        self.assertNotIn("t-prueba", json.dumps(c))

    def test_credencial_sin_variables_falla_citando_solo_nombres(self):
        m = u.preparar_entorno(cargar_env=False)
        with patch.dict(os.environ, {"AZURE_TENANT_ID": "solo-tenant"}, clear=True):
            with self.assertRaises(RuntimeError) as cm:
                m.crear_credencial()
        texto = str(cm.exception)
        self.assertIn("AZURE_CLIENT_ID", texto)
        self.assertIn("AZURE_CLIENT_SECRET", texto)
        self.assertNotIn("solo-tenant", texto)

    def test_cliente_usa_credencial_no_interactiva_con_valores_simulados(self):
        m = u.preparar_entorno(cargar_env=False)
        self.assertFalse(hasattr(m, "AzureCliCredential"), "el workflow no debe usar Azure CLI")
        secreto = "SECRETO-SIMULADO-9876543210"
        entorno = {
            "FOUNDRY_PROJECT_ENDPOINT": "https://ejemplo.invalid/api/projects/p",
            "AZURE_TENANT_ID": "tenant-simulado", "AZURE_CLIENT_ID": "client-simulado", "AZURE_CLIENT_SECRET": secreto,
        }
        with patch.dict(os.environ, entorno, clear=True):
            with patch.object(m, "ClientSecretCredential") as falsa, patch.object(m, "FoundryChatClient") as cliente:
                m.crear_cliente()
        falsa.assert_called_once_with(tenant_id="tenant-simulado", client_id="client-simulado", client_secret=secreto)
        self.assertEqual(cliente.call_args.kwargs["project_endpoint"], "https://ejemplo.invalid/api/projects/p")
        self.assertEqual(cliente.call_args.kwargs["model"], "gpt-4.1-mini")

    def test_probar_credencial_no_devuelve_el_token(self):
        m = u.preparar_entorno(cargar_env=False)

        class Token:
            token = "TOKEN-SIMULADO-NO-REAL"
            expires_on = 4102444800

        class Falsa:
            def __init__(self, **_):
                pass

            def get_token(self, ambito):
                assert ambito == "https://ai.azure.com/.default"
                return Token()

        entorno = {"AZURE_TENANT_ID": "t", "AZURE_CLIENT_ID": "c", "AZURE_CLIENT_SECRET": "s"}
        with patch.dict(os.environ, entorno, clear=True), patch.object(m, "ClientSecretCredential", Falsa):
            r = u.probar_credencial()
        self.assertTrue(r["autenticacion_correcta"])
        self.assertNotIn("TOKEN-SIMULADO", json.dumps(r))

    def test_ocultar_secretos(self):
        with patch.dict(os.environ, {"AZURE_CLIENT_SECRET": "valor-secreto-xyz"}):
            self.assertEqual(u._ocultar_secretos("fallo con valor-secreto-xyz en la peticion"), "fallo con *** en la peticion")
            self.assertNotIn("valor-secreto-xyz", u.explicar_error(RuntimeError("AADSTS7000215 clave valor-secreto-xyz")))

    def test_crear_cliente_sin_endpoint_falla_con_mensaje_claro(self):
        m = u.preparar_entorno(cargar_env=False)
        with patch.dict(os.environ, {"FOUNDRY_PROJECT_ENDPOINT": ""}):
            with patch.object(m, "PROJECT_ENDPOINT", ""):
                with self.assertRaisesRegex(RuntimeError, "FOUNDRY_PROJECT_ENDPOINT"):
                    m.crear_cliente()

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
        self.assertEqual(t.avisos, [])

    def test_explicar_error(self):
        self.assertIn("Faltan variables de autenticacion: AZURE_CLIENT_SECRET",
                      u.explicar_error(RuntimeError("Faltan variables de autenticacion: AZURE_CLIENT_SECRET. Definelas como Codespaces Secrets")))
        self.assertIn("FOUNDRY_PROJECT_ENDPOINT", u.explicar_error(RuntimeError("Falta FOUNDRY_PROJECT_ENDPOINT")))
        self.assertIn("AZURE_CLIENT_SECRET", u.explicar_error(RuntimeError("AADSTS7000215: Invalid client secret")))
        self.assertIn("AZURE_CLIENT_ID", u.explicar_error(RuntimeError("AADSTS700016: Application not found")))
        self.assertIn("rol", u.explicar_error(RuntimeError("Error code: 403 PermissionDenied")))
        self.assertNotIn("az ", u.explicar_error(RuntimeError("cualquier cosa")))


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
            texto = ruta.read_text(encoding="utf-8")
            self.assertIsNone(patron.search(texto), ruta.name)

    def test_cuaderno1_bloquea_descargas_antes_de_usar_herramientas(self):
        _, codigo = _fuentes(NB1)
        fuentes = [c.source for c in codigo]
        i_prep = next(i for i, s in enumerate(fuentes) if "preparar_entorno" in s)
        usan = [i for i, s in enumerate(fuentes) if ".func(" in s]
        self.assertTrue(usan)
        self.assertTrue(all(i > i_prep for i in usan))

    def test_cuaderno2_es_de_solo_lectura(self):
        texto = NB2.read_text(encoding="utf-8")
        self.assertNotIn("acciones_interactivas=True", texto)
        self.assertNotIn("habilitar-actualizacion-real\"", texto.split("BONUS")[0])
        self.assertNotIn("permitir_escrituras=True", texto)
        self.assertNotIn("permitir_informes=True", texto)

    def test_cuaderno2_importa_el_adaptador(self):
        _, codigo = _fuentes(NB2)
        self.assertTrue(any("entrepinares_utils" in c.source for c in codigo))

    def test_cuaderno2_no_contiene_credenciales_en_celdas(self):
        _, codigo = _fuentes(NB2)
        for c in codigo:
            self.assertNotRegex(c.source, r"(?i)client_secret\s*=\s*[\"']")
            self.assertNotRegex(c.source, r"os\.environ\[[\"']AZURE_CLIENT_SECRET")
            self.assertNotIn("print(os.environ", c.source)


PROHIBIDO = re.compile(r"az login|az account|\bazd\b|AzureCliCredential|device[- ]?code", re.IGNORECASE)


class SinAzureCliTest(unittest.TestCase):
    """Codespaces no usa Azure CLI ni inicios de sesion interactivos."""

    def _archivos(self):
        patrones = ["README.md", "docs/*.md", "notebooks/*.ipynb", "notebooks/*.py", "scripts/*", ".env.example",
                    ".devcontainer/*", "*.py", "requirements*.txt"]
        vistos = set()
        for patron in patrones:
            for ruta in RAIZ.glob(patron):
                if ruta.is_file() and ruta not in vistos:
                    vistos.add(ruta)
                    yield ruta

    def test_ningun_archivo_cita_azure_cli_ni_login_interactivo(self):
        for ruta in self._archivos():
            self.assertIsNone(PROHIBIDO.search(ruta.read_text(encoding="utf-8")), str(ruta.relative_to(RAIZ)))

    def test_devcontainer(self):
        texto = (RAIZ / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8")
        sin_comentarios = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("//"))
        cfg = json.loads(sin_comentarios)
        self.assertEqual(cfg["image"], "mcr.microsoft.com/devcontainers/python:1-3.13-bookworm")
        self.assertNotIn("features", cfg)
        self.assertNotIn("azure-cli", texto.lower())
        self.assertEqual(cfg["forwardPorts"], [8091])
        self.assertNotIn("8000", texto)
        self.assertNotIn("8088", texto)
        self.assertNotIn("secrets", cfg)
        self.assertNotIn("containerEnv", cfg)
        self.assertNotIn("build", cfg)
        self.assertEqual(sorted(cfg["customizations"]["vscode"]["extensions"]), ["ms-python.python", "ms-toolsai.jupyter"])
        self.assertIn("post-create.sh", cfg["postCreateCommand"])
        self.assertNotIn("public", sin_comentarios.lower())  # no se publican puertos
        self.assertNotIn("visibility", sin_comentarios.lower())
        self.assertTrue((RAIZ / ".devcontainer" / "post-create.sh").is_file())

    def test_post_create_instala_el_lock_linux_con_saltos_de_linea_lf(self):
        sh = (RAIZ / ".devcontainer" / "post-create.sh").read_bytes()
        self.assertNotIn(b"\r", sh)
        self.assertIn(b"requirements-codespaces.lock.txt", sh)

    def test_lock_linux(self):
        def pines(nombre):
            d = {}
            for linea in (RAIZ / nombre).read_text(encoding="utf-8").splitlines():
                m = re.match(r"^([A-Za-z0-9_.-]+)==(\S+)", linea)
                if m:
                    d[re.sub(r"[-_.]+", "-", m.group(1)).lower()] = m.group(2)
            return d

        linux, windows = pines("requirements-codespaces.lock.txt"), pines("requirements-notebook.lock.txt")
        for solo_windows in ("pywin32", "pywinpty", "colorama"):
            self.assertNotIn(solo_windows, linux)
        for comun in set(linux) & set(windows):
            self.assertEqual(linux[comun], windows[comun], comun)
        for paquete in ("agent-framework-core", "agent-framework-foundry", "agent-framework-devui",
                        "agent-framework-orchestrations", "agent-framework-openai", "azure-identity", "python-dotenv"):
            self.assertIn(paquete, linux)
        self.assertNotIn("jupyterlab", linux)


if __name__ == "__main__":
    unittest.main()
