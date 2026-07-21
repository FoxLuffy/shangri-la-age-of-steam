import { useEffect, useRef, useState } from 'react';

export default function AudioManager({ locationId, mood }: { locationId?: string; mood?: string }) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Ambient nodes
  const rumbleGainRef = useRef<GainNode | null>(null);
  const hissGainRef = useRef<GainNode | null>(null);
  
  // Music nodes
  const musicOscRef = useRef<OscillatorNode | null>(null);
  const musicGainRef = useRef<GainNode | null>(null);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    const audioEnabled = localStorage.getItem('saos_audio_enabled') !== 'false';
    
    // We wait for user interaction to start audio, standard browser policy
    const startAudio = () => {
      if (!audioEnabled) return;
      if (audioCtxRef.current) return;
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioCtxRef.current = ctx;

      // 1. Ambient Rumble
      const rumbleOsc = ctx.createOscillator();
      rumbleOsc.type = 'triangle';
      rumbleOsc.frequency.value = 40; 
      const rGain = ctx.createGain();
      rGain.gain.value = 0.3;
      rumbleOsc.connect(rGain);
      rGain.connect(ctx.destination);
      rumbleOsc.start();
      rumbleGainRef.current = rGain;

      // 2. Ambient Hiss
      const bufferSize = ctx.sampleRate * 2; 
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }
      
      const hGain = ctx.createGain();
      hGain.gain.value = 0;
      hGain.connect(ctx.destination);
      hissGainRef.current = hGain;

      setInterval(() => {
        if (!audioCtxRef.current) return;
        const noiseSource = ctx.createBufferSource();
        noiseSource.buffer = buffer;
        hGain.gain.cancelScheduledValues(ctx.currentTime);
        hGain.gain.setValueAtTime(0, ctx.currentTime);
        hGain.gain.linearRampToValueAtTime(0.1, ctx.currentTime + 0.1);
        hGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
        noiseSource.connect(hGain);
        noiseSource.start();
      }, 5000);

      // 3. Procedural Music Base
      const mOsc = ctx.createOscillator();
      mOsc.type = 'sine';
      mOsc.frequency.value = 220; // Default A3
      const mGain = ctx.createGain();
      mGain.gain.value = 0; // Silent by default
      mOsc.connect(mGain);
      mGain.connect(ctx.destination);
      mOsc.start();
      musicOscRef.current = mOsc;
      musicGainRef.current = mGain;

      setIsPlaying(true);
    };

    window.addEventListener('click', startAudio);
    window.addEventListener('keydown', startAudio);
    
    const checkInterval = setInterval(() => {
      const enabled = localStorage.getItem('saos_audio_enabled') !== 'false';
      if (!enabled && audioCtxRef.current) {
        audioCtxRef.current.close();
        audioCtxRef.current = null;
        setIsPlaying(false);
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    }, 1000);

    return () => {
      window.removeEventListener('click', startAudio);
      window.removeEventListener('keydown', startAudio);
      clearInterval(checkInterval);
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
    const targetGain = locationId === '2' ? 0.5 : 0.2; 
    rumbleGainRef.current.gain.setTargetAtTime(targetGain, ctx.currentTime, 1.0);
  }, [locationId]);

  // Update music based on mood
  useEffect(() => {
    if (!audioCtxRef.current || !musicGainRef.current || !musicOscRef.current) return;
    const ctx = audioCtxRef.current;
    
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    const mGain = musicGainRef.current;
    const mOsc = musicOscRef.current;

    mGain.gain.cancelScheduledValues(ctx.currentTime);

    if (mood === 'tense' || mood === 'bold') {
      // Fast pulsing aggressive bass
      mOsc.type = 'sawtooth';
      mGain.gain.setTargetAtTime(0.1, ctx.currentTime, 0.1);
      
      let step = 0;
      const notes = [65.41, 73.42, 65.41, 77.78]; // C2, D2, C2, D#2
      intervalRef.current = window.setInterval(() => {
        if (!audioCtxRef.current) return;
        mOsc.frequency.setValueAtTime(notes[step % notes.length], ctx.currentTime);
        mGain.gain.setValueAtTime(0.15, ctx.currentTime);
        mGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
        step++;
      }, 250);

    } else if (mood === 'cautious' || mood === 'inquisitive') {
      // Slow eerie pad
      mOsc.type = 'sine';
      mGain.gain.setTargetAtTime(0.08, ctx.currentTime, 2.0);
      
      let step = 0;
      const notes = [261.63, 293.66, 311.13, 293.66]; // C4, D4, Eb4, D4
      intervalRef.current = window.setInterval(() => {
        if (!audioCtxRef.current) return;
        mOsc.frequency.linearRampToValueAtTime(notes[step % notes.length], ctx.currentTime + 2.0);
        step++;
      }, 4000);

    } else {
      // Neutral - silence music
      mGain.gain.setTargetAtTime(0, ctx.currentTime, 2.0);
    }
  }, [mood]);

  return (
    <div className="absolute top-4 right-4 text-xs font-mono text-amber-600/50 flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isPlaying ? 'bg-green-500/50' : 'bg-red-500/50'}`} />
      {isPlaying ? 'AUDIO ACTIVE' : 'CLICK TO ENABLE AUDIO'}
    </div>
  );
}
