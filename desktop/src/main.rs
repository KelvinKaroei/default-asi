#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;
mod process_job;
use tauri::Manager;

fn main() {
    let app = tauri::Builder::default()
        .manage(backend::Backend::default())
        .invoke_handler(tauri::generate_handler![backend::backend_connection])
        .build(tauri::generate_context!())
        .expect("Falha ao iniciar a janela Default (ASI)");
    app.run(|handle, event| {
        if let tauri::RunEvent::Exit = event {
            handle.state::<backend::Backend>().stop();
        }
    });
}
