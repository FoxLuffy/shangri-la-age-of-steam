import React, { useEffect, useState } from 'react';
import './ArtifactJournal.css';

interface Artifact {
  id: number;
  name: string;
  description: string;
  stat_bonus: Record<string, number>;
  rarity: string;
}

interface ArtifactJournalProps {
  characterId: number;
  onClose: () => void;
}

export const ArtifactJournal: React.FC<ArtifactJournalProps> = ({ characterId, onClose }) => {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [discoveredIds, setDiscoveredIds] = useState<number[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/gameplay/artifacts')
      .then((res) => res.json())
      .then((data) => setArtifacts(data))
      .catch((err) => console.error('Failed to fetch artifacts', err));

    fetch(`http://localhost:8000/gameplay/characters/${characterId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.discovered_artifacts) {
          setDiscoveredIds(data.discovered_artifacts);
        }
      })
      .catch((err) => console.error('Failed to fetch character data', err));
  }, [characterId]);

  return (
    <div className="artifact-journal-overlay">
      <div className="artifact-journal-book">
        <button className="close-btn" onClick={onClose}>X</button>
        <h2 className="journal-title">Explorer's Journal</h2>
        <div className="artifact-grid">
          {artifacts.map((artifact) => {
            const isDiscovered = discoveredIds.includes(artifact.id);
            return (
              <div key={artifact.id} className={`artifact-card ${isDiscovered ? 'discovered' : 'undiscovered'}`}>
                <div className="artifact-icon">
                  {isDiscovered ? '✨' : '❓'}
                </div>
                <h3 className="artifact-name">
                  {isDiscovered ? artifact.name : 'Unknown Artifact'}
                </h3>
                {isDiscovered ? (
                  <div className="artifact-details">
                    <p className="artifact-desc">{artifact.description}</p>
                    <p className="artifact-rarity">Rarity: {artifact.rarity}</p>
                    <div className="artifact-stats">
                      {Object.entries(artifact.stat_bonus).map(([stat, bonus]) => (
                        <span key={stat} className="stat-badge">+{bonus} {stat}</span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="artifact-details">
                    <p className="artifact-desc obscured">Its secrets remain hidden...</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
