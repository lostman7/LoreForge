# LoreForge - Progress Report

## Project Overview
LoreForge is an immersive RPG AI chat application designed to provide a unique, interactive storytelling experience. The project combines a vintage RPG aesthetic with modern AI technology, allowing users to interact with characters in a rich, persistent world.

## Current System State (Initial Assessment)

### Interactive RPG Map & Dashboard
The application features a functional interactive world map (`Veridia Square`) implemented in `index.html`. Users can click on specific zones (Blacksmith, Tavern, Scribe, Guild Hall) to navigate to different character presets. A dynamic hero avatar rendering system in `renderer.js` places players on the map based on their progression.

### Combat Mechanics & Random Encounters
A turn-based combat system is implemented in `renderer.js` for "Monster Hunts" triggered from the Guild Hall. The system handles turn order, randomized damage, and visual battle logs. Monsters (Bats, Skeletons, Spiders) scale based on the player's level.

### Player Persona & Persistence
The system supports player state persistence via `persona.json`. Players can customize their stats (Level, Strength, Dexterity, etc.), backstory, and avatar. This data is used to provide context to the AI during chat sessions and to track progress across encounters.

### Economy & Shop System
A basic economy system is in place where players can earn gold through combat and spend it at character-specific shops (e.g., Thompson's Smithy). Shop inventories are dynamically managed and interact with the player's gold and inventory state.

### Initial AI & TTS Integration
The backend in `src/server.py` supports multiple AI backends (Ollama, OpenAI, Claude) and includes a framework for Text-to-Speech (TTS) using Piper and ElevenLabs. A basic typewriter effect exists in the frontend to simulate character speech, though it currently lacks the desired "Super Nintendo" timing and synchronization.

## Recently Implemented Enhancements (New Updates)

### Document Indexing (RAG Trigger)
Successfully identified and repurposed the "useless button" in the sidebar. A new `Index Documents` button is now active in the Controls section of the chat interface. This button triggers the character-specific document indexing endpoint (`/presets/{name}/index`), allowing the AI to update its local knowledge base from text files in the character's `Documents` folder in real-time.

### SNES-Style Chat Mode
Enhanced the immersion of character interactions by synchronizing the TTS output with a retro "Super Nintendo" typewriter effect.
* **Timed Delay:** Introduced a 2000ms delay after sending a message to ensure the AI's "speaking" animation (typewriter) aligns with the start of the audio generation.
* **Authentic Typewriter:** Refined the character rendering speed to 30ms per character, providing a crisp, classic RPG text display.
* **Auto-Scrolling:** Improved the chat window's auto-scroll logic to remain pinned to the bottom during the typewriter animation.

## Remaining Considerations
* **UI Customization:** Future updates could allow users to toggle the typewriter speed or choose between different retro fonts.
* **Advanced RAG Feedback:** Adding a progress bar for the document indexing process would improve the user experience for large document sets.
