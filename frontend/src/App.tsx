import { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import CharacterCreation from './components/CharacterCreation';
import StatsPanel from './components/StatsPanel';
import { fetchCharacter } from './api';
import type { Character } from './api';

function App() {
  const [characterId, setCharacterId] = useState<number | null>(() => {
    const saved = localStorage.getItem('saos_char_id');
    return saved ? parseInt(saved, 10) : null;
  });
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (characterId) {
      setLoading(true);
      fetchCharacter(characterId)
        .then(char => {
          setCharacter(char);
          localStorage.setItem('saos_char_id', char.id.toString());
        })
        .catch(err => {
          console.error(err);
          setCharacterId(null);
          localStorage.removeItem('saos_char_id');
        })
        .finally(() => setLoading(false));
    }
  }, [characterId]);

  if (loading) {
    return <div className="w-full h-screen bg-slate-950 text-amber-500 flex items-center justify-center font-mono">Loading...</div>;
  }

  if (!characterId || !character) {
    return <CharacterCreation onComplete={setCharacterId} />;
  }

  return (
    <div className="w-full h-screen bg-slate-950 flex overflow-hidden">
      <div className="flex-1 flex flex-col p-2 sm:p-4 h-full">
        <ChatInterface />
      </div>
      <StatsPanel character={character} />
    </div>
  );
}

export default App;
