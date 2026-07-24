class MockAudioManager {
  private currentMood: string = 'neutral';
  private currentAmbience: string = 'silence';

  transitionScore(mood: string) {
    if (this.currentMood === mood) return;
    console.log(`[AudioManager] Crossfading score to mood: ${mood}`);
    this.currentMood = mood;
  }

  setAmbience(locationId: string) {
    let loop = 'silence';
    if (locationId === '1') loop = 'hammering_and_steam';
    else if (locationId === '2') loop = 'wind_and_hum';
    else loop = 'ambient_drones';

    if (this.currentAmbience === loop) return;
    console.log(`[AudioManager] Setting spatial ambient loop: ${loop}`);
    this.currentAmbience = loop;
  }
}

export const audioManager = new MockAudioManager();
