// GOBLIN — App nativa de escritorio (Tauri v2)
// Al abrir: localiza el proyecto, arranca el backend Python (FastAPI) como proceso hijo,
// espera a que responda, y carga la interfaz. Al cerrar: detiene el backend.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

// Localiza la carpeta del proyecto GOBLIN probando rutas conocidas.
// Devuelve la primera que contenga backend/main.py.
fn find_project_dir() -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    // 1) Variable de entorno explícita (la más fiable).
    if let Ok(p) = std::env::var("GOBLIN_HOME") {
        candidates.push(PathBuf::from(p));
    }
    // 2) El directorio actual (modo desarrollo con run.sh).
    if let Ok(cwd) = std::env::current_dir() {
        candidates.push(cwd);
    }
    // 3) Junto al ejecutable, y un nivel arriba.
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            candidates.push(dir.to_path_buf());
            if let Some(up) = dir.parent() {
                candidates.push(up.to_path_buf());
            }
        }
    }
    // 4) Ubicaciones típicas de instalación en la home del usuario.
    if let Ok(home) = std::env::var("HOME") {
        for name in ["goblin", "Goblin", ".goblin", "GOBLIN"] {
            candidates.push(Path::new(&home).join(name));
        }
    }

    candidates
        .into_iter()
        .find(|p| p.join("backend").join("main.py").exists())
}

fn start_backend(project_dir: &Path) -> Option<Child> {
    let backend_dir = project_dir.join("backend");
    let venv_python = project_dir.join(".venv").join("bin").join("python3");
    let python = if venv_python.exists() {
        venv_python.to_string_lossy().to_string()
    } else {
        "python3".to_string()
    };

    let child = Command::new(&python)
        .arg("-m").arg("uvicorn").arg("main:app")
        .arg("--host").arg("127.0.0.1")
        .arg("--port").arg("8800")
        .current_dir(&backend_dir)
        .env("OLLAMA_NUM_PARALLEL", "1")
        .env("OLLAMA_MAX_LOADED_MODELS", "1")
        .spawn();

    match child {
        Ok(c) => {
            println!("[GOBLIN] Backend arrancado (pid {}) en {:?}", c.id(), backend_dir);
            Some(c)
        }
        Err(e) => {
            eprintln!("[GOBLIN] No se pudo arrancar el backend: {e}");
            None
        }
    }
}

// Espera (hasta ~30s) a que el backend responda en 127.0.0.1:8800.
fn wait_for_backend() -> bool {
    use std::net::TcpStream;
    for _ in 0..60 {
        if TcpStream::connect("127.0.0.1:8800").is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(500));
    }
    false
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            match find_project_dir() {
                Some(dir) => {
                    if let Some(c) = start_backend(&dir) {
                        *app.state::<BackendProcess>().0.lock().unwrap() = Some(c);
                    }
                    // Esperar a que el backend responda antes de mostrar la UI.
                    if wait_for_backend() {
                        println!("[GOBLIN] Backend listo.");
                    } else {
                        eprintln!("[GOBLIN] El backend no respondió a tiempo.");
                    }
                }
                None => {
                    eprintln!("[GOBLIN] No se encontró la carpeta del proyecto (backend/main.py). \
                               Define GOBLIN_HOME o instala el proyecto en ~/goblin.");
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Some(mut child) = window.state::<BackendProcess>().0.lock().unwrap().take() {
                    let _ = child.kill();
                    println!("[GOBLIN] Backend detenido.");
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error al arrancar GOBLIN");
}
