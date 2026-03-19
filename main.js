const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

function startPythonServer() {
  const isPackaged = app.isPackaged;
  let pythonPath;
  let args = [];

  if (isPackaged) {
    // In production, the binary is in the 'bin' folder of resources
    const binaryName = process.platform === 'win32' ? 'loreforge-server.exe' : 'loreforge-server';
    pythonPath = path.join(process.resourcesPath, 'bin', binaryName);
  } else {
    // In development, run the script directly
    pythonPath = 'python3';
    args = [path.join(__dirname, 'src', 'server.py')];
  }

  console.log(`Starting sidecar from: ${pythonPath} ${args.join(' ')}`);
  
  pythonProcess = spawn(pythonPath, args, {
    cwd: __dirname,
    env: { ...process.env, PYTHONPATH: __dirname }
  });

  pythonProcess.stdout.on('data', (data) => console.log(`Python: ${data}`));
  pythonProcess.stderr.on('data', (data) => console.error(`Python Error: ${data}`));
  
  pythonProcess.on('close', (code) => {
    console.log(`Python sidecar exited with code ${code}`);
  });
}

ipcMain.on('toggle-fullscreen', (event) => {
  if (mainWindow.isFullScreen()) {
    mainWindow.setFullScreen(false);
    mainWindow.setSize(1280, 720);
    mainWindow.center();
  } else {
    mainWindow.setFullScreen(true);
    mainWindow.setSize(1536, 1024);
  }
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    resizable: true,
    fullscreenable: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    backgroundColor: '#1a1a1a',
  });

  mainWindow.loadFile('index.html');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  startPythonServer();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (pythonProcess) pythonProcess.kill();
    app.quit();
  }
});

app.on('quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
