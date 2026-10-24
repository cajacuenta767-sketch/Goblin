// GOBLIN — App nativa de escritorio (Tauri v2)
// Al abrir: arranca el backend Python (FastAPI) como proceso hijo.
// Al cerrar: detiene el backend para no dejar procesos zombi.
// La ventana nativa carga la interfaz desde http://127.0.0.1:8800.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::Manager;

// Guarda el proceso del backend para poder detenerlo al cerrar.
struct BackendProcess(Mutex<Option<Child>>);

// Lanza el backend Python. Busca la carpeta del proyecto y ejecuta uvicorn.
fn start_backend(project_dir: &std::path::Path) -> Option<Child> {
    let backend_dir = project_dir.join("backend");
    let venv_python = project_dir.join(".venv").join("bin").join("python3");

    // Usa el python del venv si existe; si no, el del sistema.
    let python = if venv_python.exists() {
        venv_python.to_string_lossy().to_string()
    } else {
        "python3".to_string()
    };

    // Flags de Ollama para 16 GB / CPU (coherente con run.sh).
    let child = Command::new(&python)
        .arg("-m")
        .arg("uvicorn")
        .arg("main:app")
        .arg("--host").arg("127.0.0.1")
        .arg("--port").arg("8800")
        .current_dir(&backend_dir)
        .env("OLLAMA_NUM_PARALLEL", "1")
        .env("OLLAMA_MAX_LOADED_MODELS", "1")
        .spawn();

    match child {
        Ok(c) => {
            println!("[GOBLIN] Backend Python arrancado (pid {}).", c.id());
            Some(c)
        }
        Err(e) => {
            eprintln!("[GOBLIN] No se pudo arrancar el backend: {e}");
            None
        }
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // Carpeta del proyecto: junto al ejecutable, o el cwd en desarrollo.
            let project_dir = std::env::current_dir()
                .unwrap_or_else(|_| std::path::PathBuf::from("."));

            // Arranca el backend en un hilo para no bloquear la UI.
            let child = start_backend(&project_dir);
            if let Some(c) = child {
                let state = app.state::<BackendProcess>();
                *state.0.lock().unwrap() = Some(c);
            }

            // Da unos segundos al backend antes de que la ventana cargue la URL.
            thread::sleep(Duration::from_millis(1500));
            Ok(())
        })
        .on_window_event(|window, event| {
            // Al cerrar la ventana, detener el backend.
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let state = window.state::<BackendProcess>();
                if let Some(mut child) = state.0.lock().unwrap().take() {
                    let _ = child.kill();
                    println!("[GOBLIN] Backend detenido.");
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error al arrancar GOBLIN");
}
