import React, { useEffect, useRef, useState, useMemo } from 'react';
import type { Location } from '../api';

interface WorldMapProps {
  locations: Location[];
  currentLocationId: string;
  characterId: number;
  onLocationSelect: (locationId: string) => void;
  onClose: () => void;
}

interface NodeData {
  id: string;
  name: string;
  x: number;
  y: number;
  radius: number;
  controllingFaction?: string;
}

import { fetchAirship, navigateAirship } from '../api';
import AirshipPanel from './AirshipPanel';
import { factionColor, travelPoint, altitudeForProgress, humanizeFactionId } from '../utils/worldMapUtils';

const MAX_TRAVEL_ALTITUDE = 3000; // feet, for the flight readout

export default function WorldMap({ locations, currentLocationId, characterId, onLocationSelect, onClose }: WorldMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isTraveling, setIsTraveling] = useState(false);
  const [travelState, setTravelState] = useState<{fromId: string, toId: string, progress: number} | null>(null);
  const [airship, setAirship] = useState<any>(null);
  const [useAirship, setUseAirship] = useState(false);

  useEffect(() => {
    fetchAirship(characterId).then(data => {
      if (data) {
        setAirship(data);
        setUseAirship(true);
      }
    });
  }, [characterId]);

  // Generate node positions in a circle
  const nodes = useMemo<NodeData[]>(() => {
    if (locations.length === 0) return [];
    
    // We'll calculate actual x, y based on canvas size, but let's store normalized positions 0-1
    return locations.map((loc, i) => {
      const angle = (i / locations.length) * 2 * Math.PI - Math.PI / 2;
      return {
        id: loc.id,
        name: loc.name,
        // Calculate normalized positions with a bit of randomness or just a circle
        x: 0.5 + 0.35 * Math.cos(angle),
        y: 0.5 + 0.35 * Math.sin(angle),
        radius: 20,
        controllingFaction: loc.faction_id ?? undefined,
      };
    });
  }, [locations]);

  // Distinct factions present, for the legend.
  const legendFactions = useMemo(
    () => Array.from(new Set(locations.map((l) => l.faction_id).filter(Boolean))) as string[],
    [locations],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let bgImage = new Image();
    bgImage.src = '/steampunk_map_bg.jpg';

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      if (bgImage.complete && bgImage.naturalWidth > 0) {
        // Draw background
        ctx.globalAlpha = 0.4; // Darken it a bit
        ctx.drawImage(bgImage, 0, 0, width, height);
        ctx.globalAlpha = 1.0;
      } else {
        ctx.fillStyle = '#0f172a'; // slate-950
        ctx.fillRect(0, 0, width, height);
      }

      // Draw brass pipes (connections)
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      // Connect nodes in a ring, plus random cross connections
      ctx.strokeStyle = '#92400e'; // amber-800
      ctx.shadowColor = '#000';
      ctx.shadowBlur = 10;
      
      for (let i = 0; i < nodes.length; i++) {
        const current = nodes[i];
        const next = nodes[(i + 1) % nodes.length];
        
        ctx.beginPath();
        ctx.moveTo(current.x * width, current.y * height);
        ctx.lineTo(next.x * width, next.y * height);
        ctx.stroke();

        // Inner highlight for brass pipe
        ctx.strokeStyle = '#fbbf24'; // amber-400
        ctx.lineWidth = 1.5;
        ctx.shadowBlur = 0;
        ctx.stroke();
        ctx.lineWidth = 4;
        ctx.strokeStyle = '#92400e';
        ctx.shadowBlur = 10;
      }

      // Draw nodes
      nodes.forEach(node => {
        const x = node.x * width;
        const y = node.y * height;
        const isCurrent = node.id === currentLocationId;
        const isHovered = node.id === hoveredNodeId;

        // Outer brass ring
        ctx.beginPath();
        ctx.arc(x, y, node.radius + 4, 0, 2 * Math.PI);
        ctx.fillStyle = '#b45309'; // amber-700
        ctx.shadowColor = '#000';
        ctx.shadowBlur = 15;
        ctx.fill();

        // Inner core
        ctx.beginPath();
        ctx.arc(x, y, node.radius, 0, 2 * Math.PI);
        if (isCurrent) {
          ctx.fillStyle = '#38bdf8'; // sky-400
          ctx.shadowColor = '#0284c7'; // sky-600
          ctx.shadowBlur = 20;
        } else if (isHovered) {
          ctx.fillStyle = '#fbbf24'; // amber-400
          ctx.shadowColor = '#d97706'; // amber-600
          ctx.shadowBlur = 15;
        } else if (node.controllingFaction) {
          ctx.fillStyle = factionColor(node.controllingFaction);
          ctx.shadowColor = '#000';
          ctx.shadowBlur = 8;
        } else {
          ctx.fillStyle = '#1e293b'; // slate-800
          ctx.shadowBlur = 0;
        }
        ctx.fill();

        // Draw gear teeth around the ring (simplified)
        ctx.strokeStyle = '#fcd34d'; // amber-300
        ctx.lineWidth = 2;
        for (let i = 0; i < 8; i++) {
          const angle = (i / 8) * 2 * Math.PI + (isCurrent ? Date.now() / 1000 : 0);
          const r1 = node.radius + 4;
          const r2 = node.radius + 8;
          ctx.beginPath();
          ctx.moveTo(x + Math.cos(angle) * r1, y + Math.sin(angle) * r1);
          ctx.lineTo(x + Math.cos(angle) * r2, y + Math.sin(angle) * r2);
          ctx.stroke();
        }

        // Draw node name
        ctx.font = isHovered || isCurrent ? 'bold 16px "Courier New", monospace' : '14px "Courier New", monospace';
        ctx.fillStyle = isCurrent ? '#bae6fd' : '#fef3c7'; // sky-200 or amber-50
        ctx.textAlign = 'center';
        ctx.shadowColor = '#000';
        ctx.shadowBlur = 4;
        ctx.fillText(node.name, x, y + node.radius + 25);
      });

      // Draw the airship travelling along a dashed route.
      if (travelState) {
        const fromNode = nodes.find(n => n.id === travelState.fromId);
        const toNode = nodes.find(n => n.id === travelState.toId);

        if (fromNode && toNode) {
          const start = { x: fromNode.x * width, y: fromNode.y * height };
          const end = { x: toNode.x * width, y: toNode.y * height };

          // Dashed route line.
          ctx.save();
          ctx.setLineDash([10, 8]);
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#38bdf8'; // sky-400
          ctx.shadowColor = '#0284c7';
          ctx.shadowBlur = 6;
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
          ctx.restore();

          // Airship glyph (an elongated hull) oriented along the route.
          const pos = travelPoint(start, end, travelState.progress);
          const heading = Math.atan2(end.y - start.y, end.x - start.x);
          ctx.save();
          ctx.translate(pos.x, pos.y);
          ctx.rotate(heading);
          ctx.fillStyle = '#10b981'; // emerald-500
          ctx.shadowColor = '#059669';
          ctx.shadowBlur = 15;
          ctx.beginPath();
          ctx.ellipse(0, 0, 14, 6, 0, 0, 2 * Math.PI);
          ctx.fill();
          ctx.fillStyle = '#065f46'; // emerald-800 fin
          ctx.fillRect(-14, -2, 4, 4);
          ctx.restore();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    bgImage.onload = () => {
      render();
    };
    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [nodes, currentLocationId, hoveredNodeId, travelState]);

  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current && containerRef.current) {
        canvasRef.current.width = containerRef.current.clientWidth;
        canvasRef.current.height = containerRef.current.clientHeight;
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || isTraveling) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    let hovered = null;
    for (const node of nodes) {
      const nodeX = node.x * canvasRef.current.width;
      const nodeY = node.y * canvasRef.current.height;
      const dist = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);
      if (dist <= node.radius + 10) {
        hovered = node.id;
        break;
      }
    }
    setHoveredNodeId(hovered);
  };

  const handleMouseClick = (_e: React.MouseEvent<HTMLCanvasElement>) => {
    if (hoveredNodeId && hoveredNodeId !== currentLocationId && !isTraveling) {
      setIsTraveling(true);
      
      const startTime = performance.now();
      const duration = 1500; // 1.5 seconds travel time
      
      const travelAnim = (currentTime: number) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function: easeInOutQuad
        const easeProgress = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        setTravelState({
          fromId: currentLocationId,
          toId: hoveredNodeId,
          progress: easeProgress
        });
        
        if (progress < 1) {
          requestAnimationFrame(travelAnim);
        } else {
          // Airship travel does its server-side move, but the SINGLE authoritative UI travel
          // is onLocationSelect (handleLocationSwitch) which sends /chat with the destination
          // and refetches. Previously the airship also dispatched a saos_system_action that
          // re-submitted /chat at the STALE current location, flipping the character back to
          // the start at the end of the narration (reported). Removed that racy path.
          if (useAirship && airship) {
            navigateAirship(characterId, hoveredNodeId).catch((e) => console.error('Airship travel failed', e));
          }
          onLocationSelect(hoveredNodeId);
          onClose();
        }
      };
      
      requestAnimationFrame(travelAnim);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-5xl h-[80vh] bg-slate-900 border border-amber-800/60 rounded-xl shadow-[0_0_50px_rgba(180,83,9,0.3)] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-slate-950/80 border-b border-amber-900/50">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-amber-500 tracking-widest uppercase copper-gradient-text flex items-center gap-2">
              <span>🧭</span> World Map
            </h2>
            {airship && (
                <label className="flex items-center gap-2 cursor-pointer text-amber-200 text-sm">
                    <input type="checkbox" checked={useAirship} onChange={e => setUseAirship(e.target.checked)} className="accent-amber-500" />
                    Fast Travel via Airship
                </label>
            )}
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-amber-400 transition-colors"
          >
            ✕ CLOSE
          </button>
        </div>
        
        {/* Map Canvas */}
        <div className="flex-1 relative" ref={containerRef}>
          <canvas
            ref={canvasRef}
            onMouseMove={handleMouseMove}
            onClick={handleMouseClick}
            onMouseLeave={() => setHoveredNodeId(null)}
            className="absolute inset-0 w-full h-full cursor-crosshair"
            style={{ display: 'block' }}
          />
          
          {/* Overlay info */}
          {hoveredNodeId && !isTraveling && hoveredNodeId !== currentLocationId && (() => {
            const hoveredLocation = locations.find(l => l.id === hoveredNodeId);
            return (
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-950/95 border border-amber-600/50 p-4 rounded-lg text-amber-200 shadow-xl pointer-events-none max-w-lg w-full">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold font-mono text-lg">{hoveredLocation?.name}</span>
                  <span className="text-xs uppercase bg-amber-900/50 px-2 py-1 rounded animate-pulse">Click to Travel</span>
                </div>
                {hoveredLocation?.lore_text ? (
                  <p className="text-sm italic text-amber-100/80 leading-relaxed border-t border-amber-900/50 pt-2 mt-2">
                    {hoveredLocation.lore_text}
                  </p>
                ) : (
                  <p className="text-sm text-amber-400/50 italic">Location data unavailable.</p>
                )}
              </div>
            );
          })()}
          {isTraveling && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-sky-900/90 border border-sky-500/50 px-6 py-2 rounded text-sky-200 text-sm shadow-xl pointer-events-none text-center">
              <div>Traveling to destination…</div>
              {travelState && (
                <div className="text-xs text-sky-300/80 mt-1">
                  Progress {Math.round(travelState.progress * 100)}% · Altitude{' '}
                  {Math.round(altitudeForProgress(travelState.progress, MAX_TRAVEL_ALTITUDE))} ft
                </div>
              )}
            </div>
          )}

          {/* Faction territory legend */}
          {legendFactions.length > 0 && (
            <div className="absolute bottom-6 left-4 bg-slate-950/90 border border-amber-900/40 rounded-lg p-3 text-xs text-amber-100 shadow-xl pointer-events-none">
              <div className="uppercase tracking-wider text-amber-500 mb-2">Territories</div>
              <ul className="space-y-1">
                {legendFactions.map((fid) => (
                  <li key={fid} className="flex items-center gap-2">
                    <span
                      className="inline-block w-3 h-3 rounded-sm border border-black/40"
                      style={{ backgroundColor: factionColor(fid) }}
                    />
                    {humanizeFactionId(fid)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {airship && (
            <div className="absolute top-16 right-4 z-40 pointer-events-none">
                <AirshipPanel airship={airship} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
