import { useEffect, useRef, useState } from 'react';

export default function AudioManager({ locationId }: { locationId?: string }) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Oscillators and gains
  const rumbleGainRef = useRef<GainNode | null>(null);
  const hissGainRef = useRef<GainNode | null>(null);

  useEffect(() => {
    // We wait for user interaction to start audio, standard browser policy
    const startAudio = () => {
      if (audioCtxRef.current) return;
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioCtxRef.current = ctx;

      // Rumble (Low frequency sine/triangle)
      const rumbleOsc = ctx.createOscillator();
      rumbleOsc.type = 'triangle';
      rumbleOsc.frequency.value = 40; // Deep hum
      const rGain = ctx.createGain();
      rGain.gain.value = 0.3;
      rumbleOsc.connect(rGain);
      rGain.connect(ctx.destination);
      rumbleOsc.start();
      rumbleGainRef.current = rGain;

      // Hiss (White noise buffer)
      const bufferSize = ctx.sampleRate * 2; // 2 seconds
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }
      
      const hGain = ctx.createGain();
      hGain.gain.value = 0;
      hGain.connect(ctx.destination);
      hissGainRef.current = hGain;

      // Steam hiss loop
      setInterval(() => {
        if (!audioCtxRef.current) return;
        const noiseSource = ctx.createBufferSource();
        noiseSource.buffer = buffer;
        
        // Envelope for hiss
        hGain.gain.cancelScheduledValues(ctx.currentTime);
        hGain.gain.setValueAtTime(0, ctx.currentTime);
        hGain.gain.linearRampToValueAtTime(0.1, ctx.currentTime + 0.1);
        hGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
        
        noiseSource.connect(hGain);
        noiseSource.start();
      }, 5000); // Hiss every 5 seconds

      setIsPlaying(true);
    };

    window.addEventListener('click', startAudio, { once: true });
    return () => {
      window.removeEventListener('click', startAudio);
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
        audioCtxRef.current = null;
      }
    };
  }, []);

  // Update atmosphere based on location
  useEffect(() => {
    if (!audioCtxRef.current || !rumbleGainRef.current) return;
    const ctx = audioCtxRef.current;
    
    // Different areas have different rumble intensities
    const targetGain = locationId === '2' ? 0.5 : 0.2; // Location 2 is louder (e.g. factory)
    
    rumbleGainRef.current.gain.setTargetAtTime(targetGain, ctx.currentTime, 1.0);
  }, [locationId]);

  return (
    <div className="absolute top-4 right-4 text-xs font-mono text-amber-600/50 flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isPlaying ? 'bg-green-500/50' : 'bg-red-500/50'}`} />
      {isPlaying ? 'AUDIO ACTIVE' : 'CLICK TO ENABLE AUDIO'}
    </div>
  );
}
