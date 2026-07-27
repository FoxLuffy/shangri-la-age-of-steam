import React, { useEffect, useState } from 'react';
import './ArtifactJournal.css';
import { fetchJournal } from '../api';
import type { JournalData } from '../api';

interface ArtifactJournalProps {
  characterId: number;
  onClose: () => void;
}

export const ArtifactJournal: React.FC<ArtifactJournalProps> = ({ characterId, onClose }) => {
  const [journal, setJournal] = useState<JournalData>({ places: [], people: [], artifacts: [] });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!characterId) return;
    setIsLoading(true);
    fetchJournal(characterId)
      .then((data) => setJournal(data))
      .catch((err) => console.error('Failed to fetch journal', err))
      .finally(() => setIsLoading(false));
  }, [characterId]);

  const { places, people, artifacts } = journal;

  return (
    <div className="artifact-journal-overlay">
      <div className="artifact-journal-book">
        <button className="close-btn" onClick={onClose}>X</button>
        <h2 className="journal-title">Explorer's Journal</h2>

        {isLoading && <p className="journal-empty">Turning the pages...</p>}

        {!isLoading && (
          <>
            <section className="journal-section">
              <h3 className="journal-section-title">Places Discovered ({places.length})</h3>
              {places.length === 0 ? (
                <p className="journal-empty">You have not yet ventured anywhere of note.</p>
              ) : (
                <ul className="journal-list">
                  {places.map((p) => (
                    <li key={p.id}><strong>{p.name}</strong> — {p.description}</li>
                  ))}
                </ul>
              )}
            </section>

            <section className="journal-section">
              <h3 className="journal-section-title">People Met ({people.length})</h3>
              {people.length === 0 ? (
                <p className="journal-empty">You have not yet met anyone worth remembering.</p>
              ) : (
                <ul className="journal-list">
                  {people.map((n) => (
                    <li key={n.id}><strong>{n.name}</strong>{n.traits.length ? ` — ${n.traits.join(', ')}` : ''}</li>
                  ))}
                </ul>
              )}
            </section>

            <section className="journal-section">
              <h3 className="journal-section-title">Artifact Codex</h3>
              <div className="artifact-grid">
                {artifacts.map((artifact) => (
                  <div key={artifact.id} className={`artifact-card ${artifact.discovered ? 'discovered' : 'undiscovered'}`}>
                    <div className="artifact-icon">{artifact.discovered ? '✨' : '❓'}</div>
                    <h3 className="artifact-name">{artifact.discovered ? artifact.name : 'Unknown Artifact'}</h3>
                    {artifact.discovered ? (
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
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
};
