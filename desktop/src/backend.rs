use serde::Serialize;
use std::{
    io::{BufRead, BufReader, Write},
    path::Path,
    process::{Child, Command, Stdio},
    sync::{mpsc, Mutex},
    time::Duration,
};
#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[derive(Clone, Serialize)]
pub struct Connection {
    url: String,
    token: String,
}
struct Runtime {
    child: Child,
    connection: Connection,
    _job: crate::process_job::ProcessJob,
}
#[derive(Default)]
pub struct Backend(Mutex<Option<Runtime>>);

impl Backend {
    pub fn stop(&self) {
        if let Ok(mut state) = self.0.lock() {
            if let Some(mut runtime) = state.take() {
                drop(runtime.child.stdin.take());
                for _ in 0..80 {
                    if matches!(runtime.child.try_wait(), Ok(Some(_))) {
                        return;
                    }
                    std::thread::sleep(Duration::from_millis(100));
                }
                let _ = runtime.child.kill();
                let _ = runtime.child.wait();
            }
        }
    }

    fn connect(&self, resources: &Path) -> Result<Connection, String> {
        let mut state = self.0.lock().map_err(|_| "Estado do backend indisponível")?;
        if let Some(runtime) = state.as_mut() {
            if matches!(runtime.child.try_wait(), Ok(None)) {
                return Ok(runtime.connection.clone());
            }
        }
        let packaged = resources.join("backend/cyber-backend.exe");
        let mut command;
        if packaged.exists() {
            command = Command::new(&packaged);
            command.current_dir(resources);
            command.env("CYBER_OLLAMA_PATH", resources.join("ollama/ollama.exe"));
        } else if cfg!(debug_assertions) {
            let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
            let python = root.join(".venv/Scripts/python.exe");
            command = Command::new(python);
            command.args(["-m", "app"]).current_dir(root.join("backend"));
        } else {
            return Err("Backend empacotado ausente. Reinstale o aplicativo ou gere o pacote completo.".into());
        }
        let token = format!("{}{}", uuid::Uuid::new_v4().simple(), uuid::Uuid::new_v4().simple());
        command.stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        #[cfg(windows)]
        command.creation_flags(0x08000000);
        let mut child = command.spawn().map_err(|_| "Não foi possível iniciar o backend Python")?;
        let job = match crate::process_job::ProcessJob::attach(&child) {
            Ok(job) => job,
            Err(error) => { let _ = child.kill(); let _ = child.wait(); return Err(error); }
        };
        if writeln!(child.stdin.as_mut().unwrap(), "{}", serde_json::json!({"token":token})).is_err() {
            let _ = child.kill();
            let _ = child.wait();
            return Err("Falha ao iniciar a sessão local".into());
        }
        let stdout = child.stdout.take().unwrap();
        let (sender, receiver) = mpsc::channel();
        std::thread::spawn(move || {
            let mut line = String::new();
            let _ = BufReader::new(stdout).read_line(&mut line);
            let _ = sender.send(line);
        });
        let port = receiver.recv_timeout(Duration::from_secs(20)).ok()
            .and_then(|line| serde_json::from_str::<serde_json::Value>(&line).ok())
            .and_then(|value| value["port"].as_u64())
            .filter(|port| *port > 0 && *port <= 65535);
        match port {
            Some(port) => {
                let connection = Connection {
                    url: format!("http://127.0.0.1:{port}/api/v1"),
                    token,
                };
                *state = Some(Runtime { child, connection: connection.clone(), _job: job });
                Ok(connection)
            }
            None => {
                let _ = child.kill();
                let _ = child.wait();
                Err("Backend não iniciou em 20 segundos. Verifique as dependências Python.".into())
            }
        }
    }
}

#[tauri::command]
pub async fn backend_connection(
    app: tauri::AppHandle,
    window: tauri::Window,
) -> Result<Connection, String> {
    use tauri::Manager;
    if window.label() != "main" {
        return Err("Janela não autorizada".into());
    }
    let resources = app.path().resource_dir().map_err(|_| "Recursos do aplicativo indisponíveis")?;
    tauri::async_runtime::spawn_blocking(move || app.state::<Backend>().connect(&resources))
        .await.map_err(|_| "Falha ao iniciar backend".to_string())?
}
