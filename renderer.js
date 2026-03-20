// Server connection constants
const API_BASE = 'http://127.0.0.1:8000';
const WS_BASE = 'ws://127.0.0.1:8000';

// DOM Elements
const startScreen = document.getElementById('start-screen');
const enterSign = document.getElementById('enter-sign');
const dashboardView = document.getElementById('dashboard-view');
const chatView = document.getElementById('chat-container');
const battleView = document.getElementById('battle-view');
const sidebar = document.getElementById('sidebar');
const heroGrid = document.getElementById('hero-grid');
const addHeroCard = document.getElementById('add-hero-card');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const sttBtn = document.getElementById('stt-btn');
const ttsBtn = document.getElementById('tts-btn');
const configBtn = document.getElementById('config-btn');
const backToDashboardBtn = document.getElementById('back-to-dashboard');
const chatBackBtn = document.getElementById('chat-back-btn');
const backgroundLayer = document.getElementById('background-layer');
const charNameDisplay = document.getElementById('char-name-display');
const charAvatarMini = document.getElementById('char-avatar-mini');
const bgMusicStart = document.getElementById('bg-music-start');
const bgMusicGuild = document.getElementById('bg-music-guild');
const bgMusicChar = document.getElementById('bg-music-char');
const personaBtn = document.getElementById('persona-btn');
const monsterBoard = document.getElementById('monster-board');
const doorTransitionOverlay = document.getElementById('door-transition-overlay');
const doorVideo = document.getElementById('door-video');
const battleBackBtn = document.getElementById('battle-back-btn');
const battleStatus = document.getElementById('battle-status');
const battleMonsterIcon = document.getElementById('battle-monster-icon');
const battleMonsterName = document.getElementById('battle-monster-name');
const battleMonsterMeta = document.getElementById('battle-monster-meta');
const battleLog = document.getElementById('battle-log');
const battleAttackBtn = document.getElementById('battle-attack-btn');
const battleDefendBtn = document.getElementById('battle-defend-btn');
const battleFleeBtn = document.getElementById('battle-flee-btn');
const battleRerollBtn = document.getElementById('battle-reroll-btn');

// Weather elements
const weatherIcon = document.getElementById('weather-icon');
const weatherLabel = document.getElementById('weather-label');

// Modals
const modalOverlay = document.getElementById('modal-overlay');
const charModal = document.getElementById('character-modal');
const configModal = document.getElementById('config-modal');
const personaModal = document.getElementById('persona-modal');
const saveCharBtn = document.getElementById('save-char-btn');
const saveConfigBtn = document.getElementById('save-config-btn');
const savePersonaBtn = document.getElementById('save-persona-btn');
const cancelBtns = document.querySelectorAll('.cancel-btn');

let currentPreset = null;
let appConfig = null;
let isSttActive = false;
let isTtsEnabled = false;
let sttSocket = null;
let currentWeather = null;
let playerPersona = null;
let backstoryAudio = null;
let isBackstoryPlaying = false;
let battleState = null;

const MONSTER_POOL = [
    { id: 'bat', name: 'Cavern Bat', icon: '🦇', baseHp: 16, baseAttack: 4, goldReward: [10, 15], flavor: 'A screeching shadow dives through the treeline.' },
    { id: 'skeleton', name: 'Restless Skeleton', icon: '💀', baseHp: 24, baseAttack: 5, goldReward: [20, 30], flavor: 'Bone and rust stagger out from the roots with a cracked blade.' },
    { id: 'spider', name: 'Widow Spider', icon: '🕷️', baseHp: 20, baseAttack: 4, goldReward: [15, 25], flavor: 'A huge spider drops from the canopy on a silk thread.' }
];

// Weather definitions
const WEATHERS = [
    {
        id: 'sunny',
        label: 'Sunny',
        icon: 'assets/images/weather_sunny.png',
        moodPrompt: 'The weather outside is sunny and warm. You feel cheerful and energized. Occasionally reference the pleasant weather if it fits naturally.'
    },
    {
        id: 'overcast',
        label: 'Overcast',
        icon: 'assets/images/weather_overcast.png',
        moodPrompt: 'The sky is overcast with thick grey clouds. You feel contemplative and somewhat neutral. The gloomy sky makes you a touch more introspective.'
    },
    {
        id: 'rainy',
        label: 'Rainy',
        icon: 'assets/images/weather_rainy.png',
        moodPrompt: 'It is raining outside. You can hear the patter of rain. You feel a bit gloomy and melancholic. You may naturally mention the rain or the damp atmosphere.'
    },
    {
        id: 'snowy',
        label: 'Snowy',
        icon: 'assets/images/weather_snowy.png',
        moodPrompt: 'It is snowing outside. A cold chill fills the air. You feel wistful and perhaps a little cold. You may mention the snowfall or the frost if it fits.'
    }
];

// Initialize
async function waitForBackend() {
    console.log("Waiting for backend sidecar to start...");
    let attempts = 0;
    const maxAttempts = 20; // 10 seconds total
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${API_BASE}/config`);
            if (response.ok) {
                console.log("✅ Backend is reachable!");
                return true;
            }
        } catch (e) {
            // Ignore connection errors during startup
        }
        attempts++;
        await new Promise(r => setTimeout(r, 500));
    }
    console.warn("⚠️ Backend startup is taking longer than expected...");
    return false;
}

// Function to safely setup event listeners even if data load fails
function setupEventListeners() {
    console.log("Setting up event listeners...");
    
    if (enterSign) enterSign.addEventListener('click', enterGuildHall);
    
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                sendMessage();
            }
        });
    }

    if (backToDashboardBtn) backToDashboardBtn.addEventListener('click', showDashboard);
    if (chatBackBtn) chatBackBtn.addEventListener('click', showDashboard);
    if (battleBackBtn) battleBackBtn.addEventListener('click', showDashboard);
    
    if (addHeroCard) addHeroCard.addEventListener('click', () => showModal(charModal));
    
    if (monsterBoard) {
        monsterBoard.addEventListener('click', startMonsterEncounter);
    }

    if (personaBtn) {
        personaBtn.addEventListener('click', async () => {
            try {
                await loadPersona();
                showModal(personaModal);
            } catch (e) {
                console.error("Failed to open persona modal:", e);
                showModal(personaModal); // Show anyway
            }
        });
    }

    const refreshBtn = document.getElementById('refresh-presets-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            try {
                await fetch(`${API_BASE}/presets/refresh`, { method: 'POST' });
                await renderDashboard();
            } catch (e) {
                console.error("Refresh failed:", e);
            }
        });
    }

    if (configBtn) {
        configBtn.addEventListener('click', () => {
            try {
                openSettings();
                showModal(configModal);
            } catch (e) {
                console.error("Failed to open settings:", e);
                showModal(configModal);
            }
        });
    }

    if (cancelBtns) {
        cancelBtns.forEach(btn => btn.addEventListener('click', hideModals));
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) hideModals();
        });
    }

    if (saveCharBtn) saveCharBtn.addEventListener('click', createCharacter);
    if (saveConfigBtn) saveConfigBtn.addEventListener('click', saveSettings);
    if (savePersonaBtn) savePersonaBtn.addEventListener('click', savePersona);

    const toggleFullScreenBtn = document.getElementById('toggle-fullscreen-btn');
    if (toggleFullScreenBtn) {
        toggleFullScreenBtn.addEventListener('click', () => {
            try {
                window.electronAPI.toggleFullScreen();
                const statusSpan = document.getElementById('fullscreen-status');
                if (statusSpan) {
                    if (statusSpan.textContent === 'OFF') {
                        statusSpan.textContent = 'ON';
                        toggleFullScreenBtn.classList.remove('off');
                        toggleFullScreenBtn.classList.add('on');
                    } else {
                        statusSpan.textContent = 'OFF';
                        toggleFullScreenBtn.classList.remove('on');
                        toggleFullScreenBtn.classList.add('off');
                    }
                }
            } catch (e) {
                console.error("Fullscreen toggle failed:", e);
            }
        });
    }

    if (ttsBtn) ttsBtn.addEventListener('click', toggleTTS);
    if (sttBtn) sttBtn.addEventListener('click', toggleSTT);

    const personaAvatarUpload = document.getElementById('persona-avatar-upload');
    if (personaAvatarUpload) {
        personaAvatarUpload.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    const preview = document.getElementById('persona-avatar-preview');
                    if (preview) preview.innerHTML = `<img src="${ev.target.result}" alt="Preview">`;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (battleAttackBtn) battleAttackBtn.addEventListener('click', () => resolveBattleTurn('attack'));
    if (battleDefendBtn) battleDefendBtn.addEventListener('click', () => resolveBattleTurn('defend'));
    if (battleFleeBtn) battleFleeBtn.addEventListener('click', fleeBattle);
    if (battleRerollBtn) battleRerollBtn.addEventListener('click', startMonsterEncounter);

    const backstoryToggleBtn = document.getElementById('backstory-toggle-btn');
    if (backstoryToggleBtn) {
        backstoryToggleBtn.addEventListener('click', toggleBackstory);
    }
    
    console.log("Event listeners setup complete.");
}

async function init() {
    console.log("🚀 Starting initialization...");
    
    // 1. Immediately setup listeners and show start screen
    setupEventListeners();
    showStartScreen();

    try {
        // Set volumes
        if (bgMusicStart) bgMusicStart.volume = 0.35;
        if (bgMusicGuild) bgMusicGuild.volume = 0.35;
        if (bgMusicChar) bgMusicChar.volume = 0.35;

        // 2. Wait for backend
        const backendReady = await waitForBackend();
        if (!backendReady) {
            console.error("❌ Backend not reached. Some features will be unavailable.");
            return;
        }

        // 3. Try initial loads
        console.log("Loading configuration...");
        try { await loadConfig(); } catch (e) { console.error("Config load error:", e); }
        
        console.log("Rendering hero grid...");
        try { await renderDashboard(); } catch (e) { console.error("Hero grid render error:", e); }

        console.log("Loading persona...");
        try { await loadPersona(); } catch (e) { console.error("Persona load error:", e); }
        
        console.log("Initializing WebSocket...");
        try { initWebSocket(); } catch (e) { console.error("WS initialization error:", e); }
        
        console.log("✨ Initialization complete!");
    } catch (criticalErr) {
        console.error("🔥 CRITICAL INIT FAILURE:", criticalErr);
    }
}

function showStartScreen() {
    startScreen.classList.remove('hidden');
    dashboardView.classList.add('hidden');
    chatView.classList.add('hidden');
    battleView.classList.add('hidden');
    sidebar.classList.add('hidden');

    // Music
    if (bgMusicGuild) bgMusicGuild.pause();
    if (bgMusicStart) {
        bgMusicStart.currentTime = 0;
        bgMusicStart.play().catch(e => console.log("Start music blocked"));
    }
}

async function enterGuildHall() {
    startScreen.classList.add('hidden');
    
    // Switch music
    if (bgMusicStart) bgMusicStart.pause();
    if (bgMusicGuild) {
        bgMusicGuild.currentTime = 0;
        bgMusicGuild.play().catch(e => console.log("Guild music blocked"));
    }

    // Refresh dashboard to ensure we have the latest characters
    await renderDashboard();
    showDashboard();
}

function showDashboard() {
    dashboardView.classList.remove('hidden');
    chatView.classList.add('hidden');
    battleView.classList.add('hidden');
    sidebar.classList.add('hidden');
    currentWeather = null;

    // Stop character music and resume guild music
    if (bgMusicChar) bgMusicChar.pause();
    if (bgMusicGuild && bgMusicGuild.paused) {
        bgMusicGuild.play().catch(e => console.log("Guild music blocked"));
    }
}

function getPersonaLevel() {
    return Math.max(1, parseInt(playerPersona?.stats?.level, 10) || 1);
}

function getMonsterLevelForPlayer(playerLevel) {
    if (playerLevel >= 6) return 3;
    if (playerLevel >= 4) return 2;
    return 1;
}

function appendBattleLog(text, type = 'system') {
    if (!battleLog) return;
    const entry = document.createElement('div');
    entry.className = `battle-log-entry ${type}`;
    entry.textContent = text;
    battleLog.appendChild(entry);
    battleLog.scrollTop = battleLog.scrollHeight;
}

function refreshBattleUi() {
    if (!battleState) return;

    const { monster, player } = battleState;
    battleMonsterIcon.textContent = monster.icon;
    battleMonsterName.textContent = `${monster.name} — Lv.${monster.level}`;
    battleMonsterMeta.textContent = `Forest encounter. ${monster.flavor} HP ${monster.hp}/${monster.maxHp} • Your HP ${player.hp}/${player.maxHp}`;
    battleStatus.textContent = `${player.name} Lv.${player.level} • HP ${player.hp}/${player.maxHp} • ${monster.name} HP ${monster.hp}/${monster.maxHp}`;

    const disabled = battleState.finished;
    battleAttackBtn.disabled = disabled;
    battleDefendBtn.disabled = disabled;
    battleFleeBtn.disabled = disabled;
}

function showBattleView() {
    startScreen.classList.add('hidden');
    dashboardView.classList.add('hidden');
    chatView.classList.add('hidden');
    sidebar.classList.add('hidden');
    battleView.classList.remove('hidden');
    if (bgMusicChar) bgMusicChar.pause();
    if (bgMusicGuild && bgMusicGuild.paused) {
        bgMusicGuild.play().catch(() => {});
    }
}

function startMonsterEncounter() {
    const playerName = playerPersona?.name?.trim() || 'Traveler';
    const playerLevel = getPersonaLevel();
    const monsterLevel = getMonsterLevelForPlayer(playerLevel);
    const template = MONSTER_POOL[Math.floor(Math.random() * MONSTER_POOL.length)];
    const maxHp = template.baseHp + (monsterLevel - 1) * 8;

    battleState = {
        finished: false,
        player: {
            name: playerName,
            level: playerLevel,
            maxHp: 28 + playerLevel * 8,
            hp: 28 + playerLevel * 8,
            defending: false,
        },
        monster: {
            ...template,
            level: monsterLevel,
            maxHp,
            hp: maxHp,
        },
    };

    battleLog.innerHTML = '';
    appendBattleLog(`${playerName} accepts a forest contract from the guild hall board.`, 'system');
    appendBattleLog(`A ${battleState.monster.name} (Lv.${monsterLevel}) appears. ${battleState.monster.flavor}`, 'monster');
    appendBattleLog(`Scaling rule: player Lv.${playerLevel} faces monster Lv.${monsterLevel}.`, 'system');
    showBattleView();
    refreshBattleUi();
}

function resolveBattleTurn(action) {
    if (!battleState || battleState.finished) return;

    const { player, monster } = battleState;
    player.defending = action === 'defend';

    if (action === 'attack') {
        const damage = 4 + Math.floor(Math.random() * 6) + Math.max(0, player.level - 1);
        monster.hp = Math.max(0, monster.hp - damage);
        appendBattleLog(`${player.name} strikes ${monster.name} for ${damage} damage.`, 'user');
    } else if (action === 'defend') {
        appendBattleLog(`${player.name} braces for the next hit and tightens their guard.`, 'system');
    }

    if (monster.hp <= 0) {
        battleState.finished = true;

        // Grant Gold Reward
        const minGold = monster.goldReward[0];
        const maxGold = monster.goldReward[1];
        const goldWon = Math.floor(Math.random() * (maxGold - minGold + 1)) + minGold;

        if (!playerPersona.gold) playerPersona.gold = 0;
        playerPersona.gold += goldWon;

        appendBattleLog(`${monster.name} falls. The forest path is clear—for now.`, 'system');
        appendBattleLog(`Victory! You found ${goldWon} gold on the creature.`, 'system');

        // Persist new gold to server
        savePersona();

        refreshBattleUi();
        return;
    }

    let monsterDamage = monster.baseAttack + (monster.level - 1) * 2 + Math.floor(Math.random() * 4);
    if (player.defending) {
        monsterDamage = Math.max(1, monsterDamage - (3 + Math.floor(player.level / 2)));
    }

    player.hp = Math.max(0, player.hp - monsterDamage);
    appendBattleLog(`${monster.name} hits back for ${monsterDamage} damage.`, 'monster');
    player.defending = false;

    if (player.hp <= 0) {
        battleState.finished = true;
        appendBattleLog(`${player.name} is beaten back and retreats to the guild hall to recover.`, 'system');
    }

    refreshBattleUi();
}

function fleeBattle() {
    if (!battleState || battleState.finished) return;
    battleState.finished = true;
    appendBattleLog(`${battleState.player.name} disengages and escapes back toward the guild hall.`, 'system');
    refreshBattleUi();
}

async function showChat(presetName) {
    // Show door transition video
    if (doorTransitionOverlay && doorVideo) {
        try {
            doorTransitionOverlay.classList.remove('hidden');
            doorVideo.currentTime = 0;
            
            // Use a promise to wait for the video to finish
            const videoFinished = new Promise((resolve) => {
                doorVideo.onended = resolve;
                // Fallback timeout in case video fails to load or play (e.g. 3 seconds)
                setTimeout(resolve, 3000);
            });

            doorVideo.play().catch(e => {
                console.warn("Door video play failed", e);
            });

            await videoFinished;
        } finally {
            doorTransitionOverlay.classList.add('hidden');
            doorVideo.pause();
        }
    }

    dashboardView.classList.add('hidden');
    chatView.classList.remove('hidden');
    sidebar.classList.remove('hidden');
    
    // Pause guild music
    if (bgMusicGuild) bgMusicGuild.pause();

    // Randomly select weather
    selectRandomWeather();
    
    await loadPresetDetails(presetName);
}

function selectRandomWeather() {
    const idx = Math.floor(Math.random() * WEATHERS.length);
    currentWeather = WEATHERS[idx];
    
    if (weatherIcon) {
        weatherIcon.src = currentWeather.icon;
        weatherIcon.alt = currentWeather.label;
    }
    if (weatherLabel) {
        weatherLabel.textContent = currentWeather.label;
    }
}

function initWebSocket() {
    try {
        sttSocket = new WebSocket(`${WS_BASE}/ws/stt`);
        
        sttSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'stt_result') {
                messageInput.value += (messageInput.value ? ' ' : '') + data.text;
                messageInput.focus();
            }
        };

        sttSocket.onclose = () => {
            setTimeout(initWebSocket, 2000);
        };
    } catch (e) {
        console.log("WebSocket connection failed, retrying...");
        setTimeout(initWebSocket, 2000);
    }
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        appConfig = await response.json();
    } catch (err) {
        console.error('Failed to load config:', err);
    }
}

async function renderDashboard() {
    try {
        const response = await fetch(`${API_BASE}/presets`);
        const presets = await response.json();
        
        // Clear existing tiles except the "Add" card
        const existingTiles = heroGrid.querySelectorAll('.hero-tile:not(.add-hero)');
        existingTiles.forEach(tile => tile.remove());

        presets.forEach(preset => {
            const tile = document.createElement('div');
            tile.className = 'hero-tile';
            
            if (preset.avatar_path) {
                const img = document.createElement('img');
                img.className = 'tile-avatar';
                img.src = `file://${preset.avatar_path}`;
                tile.appendChild(img);
            }

            const name = document.createElement('div');
            name.className = 'tile-name';
            name.textContent = preset.character_name;
            tile.appendChild(name);

            tile.addEventListener('click', () => showChat(preset.name));
            
            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-char-btn';
            deleteBtn.innerHTML = 'X';
            deleteBtn.title = 'Delete Character';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteCharacter(preset.name, preset.character_name);
            });
            tile.appendChild(deleteBtn);

            heroGrid.appendChild(tile);
        });
    } catch (err) {
        console.error('Failed to load presets:', err);
    }
}

async function loadPresetDetails(name) {
    try {
        const response = await fetch(`${API_BASE}/presets/${name}`);
        currentPreset = await response.json();
        
        charNameDisplay.textContent = currentPreset.config.character_name;
        if (currentPreset.avatar_path) {
            charAvatarMini.src = `file://${currentPreset.avatar_path}`;
            charAvatarMini.classList.remove('hidden');
        } else {
            charAvatarMini.classList.add('hidden');
        }

        if (currentPreset.background_frames && currentPreset.background_frames.length > 0) {
            backgroundLayer.style.backgroundImage = `url('file://${currentPreset.background_frames[0]}')`;
        } else {
            backgroundLayer.style.backgroundImage = 'none';
        }

        // Handle character background music
        if (bgMusicChar) {
            if (currentPreset.music_path) {
                bgMusicChar.src = `file://${currentPreset.music_path}`;
                bgMusicChar.currentTime = 0;
                bgMusicChar.play().catch(e => console.log("Character music blocked"));
            } else {
                bgMusicChar.pause();
                bgMusicChar.src = "";
            }
        }

        // Handle backstory audio
        if (battleAttackBtn) battleAttackBtn.addEventListener('click', () => resolveBattleTurn('attack'));
    if (battleDefendBtn) battleDefendBtn.addEventListener('click', () => resolveBattleTurn('defend'));
    if (battleFleeBtn) battleFleeBtn.addEventListener('click', fleeBattle);
    if (battleRerollBtn) battleRerollBtn.addEventListener('click', startMonsterEncounter);

    const backstoryToggleBtn = document.getElementById('backstory-toggle-btn');
        if (currentPreset.backstory_audio_path) {
            backstoryToggleBtn.classList.remove('hidden');
            if (backstoryAudio) {
                backstoryAudio.pause();
                backstoryAudio = null;
            }
            backstoryAudio = new Audio(`file://${currentPreset.backstory_audio_path}`);
            isBackstoryPlaying = false;
            backstoryToggleBtn.classList.remove('active');
        } else {
            backstoryToggleBtn.classList.add('hidden');
        }

        chatMessages.innerHTML = '';
        
        // Build intro message with persona if available
        let introMsg = `Character loaded: ${currentPreset.config.character_name}.`;
        if (currentWeather) {
            introMsg += ` The weather today is ${currentWeather.label.toLowerCase()}.`;
        }
        if (playerPersona && playerPersona.name) {
            introMsg += ` Speaking with ${playerPersona.name}.`;
        }
        introMsg += ' How can I help you today?';
        
        addMessage('ai', introMsg, currentPreset.config.character_name);
    } catch (err) {
        console.error('Failed to load preset details:', err);
    }
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentPreset) return;

    const player = playerPersona && playerPersona.name ? playerPersona.name : document.getElementById('player-select').value;
    messageInput.value = '';

    addMessage('user', text, player);

    try {
        const body = {
            message: text,
            player: player,
            tts_enabled: isTtsEnabled
        };

        // Add weather context
        if (currentWeather) {
            body.weather = currentWeather.id;
            body.weather_prompt = currentWeather.moodPrompt;
        }

        // Add persona context
        if (playerPersona && playerPersona.name) {
            body.persona = {
                name: playerPersona.name,
                backstory: playerPersona.backstory || '',
                gold: playerPersona.gold || 0,
                stats: playerPersona.stats || {}
            };
        }

        const response = await fetch(`${API_BASE}/presets/${currentPreset.name}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const result = await response.json();

        if (isTtsEnabled) {
            // Delay AI response to sync with TTS start
            setTimeout(() => {
                addMessage('ai', result.response, currentPreset.config.character_name);
            }, 1000);
        } else {
            addMessage('ai', result.response, currentPreset.config.character_name);
        }
    } catch (err) {
        console.error('Failed to send message:', err);
        addMessage('ai', 'Chat Error: Could not connect to AI server.', 'System');
    }
}

function addMessage(type, text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    const senderSpan = document.createElement('span');
    senderSpan.className = 'sender';
    senderSpan.textContent = sender;
    const textDiv = document.createElement('div');
    textDiv.className = 'text';
    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(textDiv);
    chatMessages.appendChild(msgDiv);

    if (type === 'ai' && isTtsEnabled) {
        // SNES-style typewriter effect
        const chars = Array.from(text);
        let i = 0;
        textDiv.textContent = '';
        const interval = setInterval(() => {
            textDiv.textContent += chars[i];
            i++;
            chatMessages.scrollTop = chatMessages.scrollHeight;
            if (i >= chars.length) {
                clearInterval(interval);
            }
        }, 35); // Approx 30-40ms per character
    } else {
        textDiv.textContent = text;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function toggleBackstory() {
    if (!backstoryAudio) return;
    const btn = document.getElementById('backstory-toggle-btn');

    if (isBackstoryPlaying) {
        backstoryAudio.pause();
        isBackstoryPlaying = false;
        btn.classList.remove('active');
    } else {
        backstoryAudio.play().catch(e => console.error("Backstory audio play failed", e));
        isBackstoryPlaying = true;
        btn.classList.add('active');
    }
}

async function deleteCharacter(name, displayName) {
    if (!confirm(`Are you sure you want to delete ${displayName}? This cannot be undone.`)) return;

    try {
        const response = await fetch(`${API_BASE}/presets/${name}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        alert(result.message);
        await renderDashboard();
    } catch (err) {
        console.error('Failed to delete character:', err);
        alert('Failed to delete character');
    }
}

// ========================================
// Character Creation (with file uploads)
// ========================================

async function createCharacter() {
    const name = document.getElementById('char-name').value;
    const role = document.getElementById('char-role').value;
    const location = document.getElementById('char-location').value;
    const description = document.getElementById('char-desc').value;
    const avatarFile = document.getElementById('char-avatar-upload').files[0];
    const bgFile = document.getElementById('char-bg-upload').files[0];
    const musicFile = document.getElementById('char-music-upload').files[0];
    const ragFile = document.getElementById('char-rag-upload').files[0];
    const backstoryAudioFile = document.getElementById('char-backstory-audio-upload').files[0];

    if (!name) return alert('Name is required');

    // Read files as base64
    let avatarData = null;
    let bgData = null;
    let musicData = null;
    let ragData = null;
    let backstoryAudioData = null;

    if (avatarFile) {
        avatarData = await readFileAsBase64(avatarFile);
    }
    if (bgFile) {
        bgData = await readFileAsBase64(bgFile);
    }
    if (musicFile) {
        musicData = await readFileAsBase64(musicFile);
    }
    if (ragFile) {
        ragData = await readFileAsBase64(ragFile);
    }
    if (backstoryAudioFile) {
        backstoryAudioData = await readFileAsBase64(backstoryAudioFile);
    }

    const data = {
        name: name,
        role: role,
        location: location,
        description: description,
        avatar_image: avatarData,
        background_image: bgData,
        music_data: musicData,
        rag_data: ragData,
        backstory_audio: backstoryAudioData
    };

    try {
        const response = await fetch(`${API_BASE}/presets/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        alert(result.message);
        hideModals();
        // Clear form
        document.getElementById('char-name').value = '';
        document.getElementById('char-role').value = '';
        document.getElementById('char-location').value = '';
        document.getElementById('char-desc').value = '';
        document.getElementById('char-avatar-upload').value = '';
        document.getElementById('char-bg-upload').value = '';
        document.getElementById('char-music-upload').value = '';
        document.getElementById('char-rag-upload').value = '';
        document.getElementById('char-backstory-audio-upload').value = '';
        await renderDashboard();
    } catch (err) {
        alert('Failed to create character');
    }
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Remove the data:image/...;base64, prefix
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ========================================
// Player Persona
// ========================================

async function loadPersona() {
    try {
        const response = await fetch(`${API_BASE}/persona`);
        if (!response.ok) throw new Error('Failed to load persona');
        const data = await response.json();
        
        playerPersona = data;
        
        // Update UI
        if (playerPersona) {
            document.getElementById('persona-name').value = playerPersona.name || '';
            document.getElementById('persona-backstory').value = playerPersona.backstory || '';
            
            if (playerPersona.stats) {
                document.getElementById('persona-level').value = playerPersona.stats.level || 1;
                document.getElementById('persona-strength').value = playerPersona.stats.strength || 10;
                document.getElementById('persona-dexterity').value = playerPersona.stats.dexterity || 10;
                document.getElementById('persona-intelligence').value = playerPersona.stats.intelligence || 10;
                document.getElementById('persona-charisma').value = playerPersona.stats.charisma || 10;
                document.getElementById('persona-wisdom').value = playerPersona.stats.wisdom || 10;
            }

            if (playerPersona.avatar) {
                const preview = document.getElementById('persona-avatar-preview');
                preview.innerHTML = `<img src="${playerPersona.avatar}" alt="Preview">`;
            }
        }
    } catch (error) {
        console.error('Error loading persona from server:', error);
        // Fallback to local storage
        const saved = localStorage.getItem('loreforge_persona');
        if (saved) {
            playerPersona = JSON.parse(saved);
            // ... (populate UI if needed, but it's cleaner to just let the server move be the source of truth)
        }
    }
}

async function savePersona() {
    const name = document.getElementById('persona-name').value.trim();
    if (!name) return alert('Please enter a name for your persona.');

    const avatarFile = document.getElementById('persona-avatar-upload').files[0];
    let avatarDataUrl = playerPersona?.avatar || null;

    if (avatarFile) {
        avatarDataUrl = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(avatarFile);
        });
    }

    playerPersona = {
        name: name,
        backstory: document.getElementById('persona-backstory').value,
        avatar: avatarDataUrl,
        gold: playerPersona?.gold || 0,
        stats: {
            level: parseInt(document.getElementById('persona-level').value) || 1,
            strength: parseInt(document.getElementById('persona-strength').value) || 10,
            dexterity: parseInt(document.getElementById('persona-dexterity').value) || 10,
            intelligence: parseInt(document.getElementById('persona-intelligence').value) || 10,
            charisma: parseInt(document.getElementById('persona-charisma').value) || 10,
            wisdom: parseInt(document.getElementById('persona-wisdom').value) || 10
        }
    };

    localStorage.setItem('loreforge_persona', JSON.stringify(playerPersona));

    // Save to server
    try {
        await fetch(`${API_BASE}/persona`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(playerPersona)
        });
    } catch (error) {
        console.error('Error saving persona to server:', error);
    }

    // Also update the player select dropdown
    const playerSelect = document.getElementById('player-select');
    if (playerSelect) {
        let exists = false;
        for (let i = 0; i < playerSelect.options.length; i++) {
            if (playerSelect.options[i].value === playerPersona.name) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            const opt = document.createElement('option');
            opt.value = playerPersona.name;
            opt.textContent = playerPersona.name;
            playerSelect.appendChild(opt);
        }
        playerSelect.value = playerPersona.name;
    }

    alert('Persona saved!');
    hideModals();
}

// ========================================
// Config
// ========================================

async function openSettings() {
    await loadConfig();
    const configModal = document.getElementById('config-modal');
    
    document.getElementById('ai-backend').value = appConfig.ai?.backend || 'ollama';
    document.getElementById('ai-backend').value = appConfig.ai?.backend || 'ollama';
    document.getElementById('ai-num-ctx').value = appConfig.ai?.num_ctx || 4096;
    
    // API Keys
    document.getElementById('key-openai').value = appConfig.apis?.openai || '';
    document.getElementById('key-claude').value = appConfig.apis?.claude || '';
    document.getElementById('key-grok').value = appConfig.apis?.grok || '';
    document.getElementById('key-llama-cloud').value = appConfig.apis?.llama_cloud || '';

    // Fetch and populate models
    const modelSelect = document.getElementById('model-select');
    if (modelSelect) {
        modelSelect.innerHTML = '<option value="">-- Loading models... --</option>';
        
        try {
            const response = await fetch(`${API_BASE}/ai/models`);
            const models = await response.json();
            
            modelSelect.innerHTML = '<option value="">-- Select a Model --</option>';
            models.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model;
                opt.textContent = model;
                if (model === appConfig.ai?.model) {
                    opt.selected = true;
                }
                modelSelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to fetch models:', err);
            modelSelect.innerHTML = '<option value="">-- Failed to load models --</option>';
        }
    }

    configModal.classList.remove('hidden');
}

async function saveSettings() {
    const backend = document.getElementById('ai-backend').value;
    const model = document.getElementById('model-select').value;
    const numCtx = parseInt(document.getElementById('ai-num-ctx').value) || 4096;

    const newConfig = {
        ...appConfig,
        ai: {
            ...appConfig.ai,
            backend: backend,
            model: model,
            num_ctx: numCtx
        },
        apis: {
            ...appConfig.apis,
            openai: document.getElementById('key-openai').value,
            claude: document.getElementById('key-claude').value,
            grok: document.getElementById('key-grok').value,
            llama_cloud: document.getElementById('key-llama-cloud').value
        }
    };

    try {
        const response = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });

        if (response.ok) {
            appConfig = newConfig;
            alert('Settings saved! You may need to restart for some changes to take effect.');
            document.getElementById('config-modal').classList.add('hidden');
        }
    } catch (err) {
        console.error('Failed to save settings:', err);
        alert('Failed to save settings');
    }
}

async function toggleSTT() {
    isSttActive = !isSttActive;
    sttBtn.classList.toggle('active');
    sttBtn.textContent = isSttActive ? 'Stop STT' : 'Start STT';
    await fetch(`${API_BASE}/stt/${isSttActive ? 'start' : 'stop'}`, { method: 'POST' });
}

async function toggleTTS() {
    isTtsEnabled = !isTtsEnabled;
    if (ttsBtn) {
        ttsBtn.classList.toggle('active');
        ttsBtn.textContent = isTtsEnabled ? '🔊 Voice: ON' : '🔊 Voice: OFF';
    }
}

function showModal(modal) {
    modalOverlay.classList.remove('hidden');
    modal.classList.remove('hidden');
}

function hideModals() {
    modalOverlay.classList.add('hidden');
    charModal.classList.add('hidden');
    configModal.classList.add('hidden');
    personaModal.classList.add('hidden');
}

init();
