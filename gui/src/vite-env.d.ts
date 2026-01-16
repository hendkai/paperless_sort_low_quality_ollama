/// <reference types="vite/client" />
/// <reference types="vite-plugin-electron/electron-env" />

interface Window {
    ipcRenderer: import('electron').IpcRenderer
}
