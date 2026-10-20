let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  const AC =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  if (!ctx) ctx = new AC();
  return ctx;
}

/** Browsers only allow sound after a click or key press. */
export function unlockStairsAlert() {
  const ac = audio();
  if (!ac) return;
  if (ac.state === "suspended") void ac.resume();
}

/**
 * One long deep horn when someone comes up the stairs.
 * A pure sub-bass sine disappears on laptop speakers, so the body sits
 * around 100 Hz and a low-pass filter keeps it dark.
 */
export async function playStairsAlert() {
  const ac = audio();
  if (!ac) return;
  if (ac.state !== "running") {
    try {
      await ac.resume();
    } catch {
      return;
    }
  }
  if (ac.state !== "running") return;

  const now = ac.currentTime + 0.03;
  const filter = ac.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.setValueAtTime(220, now);
  filter.frequency.exponentialRampToValueAtTime(140, now + 2.1);
  filter.Q.value = 0.85;

  const master = ac.createGain();
  master.gain.setValueAtTime(0.0001, now);
  master.gain.exponentialRampToValueAtTime(0.92, now + 0.12);
  master.gain.setValueAtTime(0.92, now + 1.35);
  master.gain.exponentialRampToValueAtTime(0.0001, now + 2.35);
  master.connect(filter);
  filter.connect(ac.destination);

  const horn = (freq: number, type: OscillatorType, level: number) => {
    const osc = ac.createOscillator();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(Math.max(40, freq * 0.72), now + 2.15);
    const gain = ac.createGain();
    gain.gain.setValueAtTime(level, now);
    osc.connect(gain);
    gain.connect(master);
    osc.start(now);
    osc.stop(now + 2.4);
  };

  horn(108, "sawtooth", 0.34);
  horn(54, "sine", 0.8);
  horn(81, "triangle", 0.22);
}
