const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add any IPC methods here if needed
  on: (channel, callback) => ipcRenderer.on(channel, (event, ...args) => callback(...args)),
    toggleFullScreen: () => ipcRenderer.send('toggle-fullscreen'),
});
