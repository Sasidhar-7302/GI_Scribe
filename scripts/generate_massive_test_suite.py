import os
import json
import asyncio
import random
from pathlib import Path

try:
    import edge_tts
    from pydub import AudioSegment
except ImportError:
    print("Please install prerequisites: pip install edge-tts pydub")
    exit(1)

OUTPUT_DIR = Path("data/GiAudiotest")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_DIR = Path("data/training_corpus/chunks")
TRAIN_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_FILE = Path("data/manual_scripts.json")

VOICE_DOCTOR = "en-US-ChristopherNeural"
VOICE_PATIENT = "en-US-JennyNeural"

# Pool of unique clinical small talk / ROS / History to expand duration
ROS_POOL = [
    ("Doctor", "How is your appetite generally? Are you able to enjoy your meals?"),
    ("Patient", "It's hit or miss. Some days I'm starving, other days the smell of food makes me nauseous."),
    ("Doctor", "Have you noticed any changes in your energy levels throughout the day?"),
    ("Patient", "I'm usually okay in the morning, but by two o'clock, I feel like I need a three-hour nap."),
    ("Doctor", "Are you sleeping well at night? Any trouble falling asleep or staying asleep?"),
    ("Patient", "I wake up a few times, usually because I can't get comfortable, or my stomach is gurgling."),
    ("Doctor", "Do you have any known allergies to medications, specifically antibiotics or pain relievers?"),
    ("Patient", "Only Penicillin. It gave me a nasty rash when I was a kid."),
    ("Doctor", "How much water are you drinking in a typical day?"),
    ("Patient", "Probably not enough. Maybe three or four glasses. I drink a lot of coffee though."),
    ("Doctor", "Have you had any recent travel outside of the country, perhaps to a place where the water might not be safe?"),
    ("Patient", "No, I haven't left the state in over a year."),
    ("Doctor", "Any history of thyroid issues or diabetes in your family?"),
    ("Patient", "My mother has a slow thyroid, but as far as I know, I'm okay."),
    ("Doctor", "How about your blood pressure? Do you monitor that at home?"),
    ("Patient", "The pharmacy machine usually says it's around 130 over 85. A little high, I think."),
    ("Doctor", "Have you noticed any swelling in your legs or ankles at the end of the day?"),
    ("Patient", "Sometimes if I've been standing a lot, but usually they look normal in the morning."),
    ("Doctor", "Are you taking any herbal supplements, vitamins, or probiotics that I should know about?"),
    ("Patient", "I take a multivitamin and some Vitamin D in the winter."),
    ("Doctor", "Do you exercise regularly? What kind of activity do you do?"),
    ("Patient", "I try to walk the dog for thirty minutes every evening, weather permitting."),
    ("Doctor", "Have you noticed any changes in your skin, like unusual dryness or new marks?"),
    ("Patient", "Just the typical dry skin I get when the heater is on."),
    ("Doctor", "How about your vision? Any new blurriness or headaches?"),
    ("Patient", "My eyes get tired at the computer, but no real changes."),
    ("Doctor", "Any history of kidney stones or frequent urinary tract infections?"),
    ("Patient", "I had a kidney stone about ten years ago. One was enough for a lifetime."),
    ("Doctor", "Have you noticed any shortness of breath when you're walking up stairs?"),
    ("Patient", "Maybe a little, but I usually just think I'm out of shape."),
    ("Doctor", "Do you have any history of heart palpitations or a racing heart?"),
    ("Patient", "Only when I have too much caffeine in the morning."),
    ("Doctor", "Any chest tightness or pressure that comes on with exertion?"),
    ("Patient", "No, nothing like that. My heart feels fine."),
    ("Doctor", "Have you noticed any numbness or tingling in your hands or feet?"),
    ("Patient", "Occasionally in my left foot if I sit in one position for too long."),
    ("Doctor", "Are you having any pain or stiffness in your neck or shoulders?"),
    ("Patient", "A bit of tension from my desk job, but nothing major."),
    ("Doctor", "Any history of seizures, fainting, or blackouts?"),
    ("Patient", "No, never had anything like that."),
    ("Doctor", "Have you noticed any unusual bruising or bleeding when you brush your teeth?"),
    ("Patient", "My gums bleed a little if I haven't flossed in a few days."),
    ("Doctor", "How has your mood been lately? Feeling particularly anxious or down?"),
    ("Patient", "The stomach issues have me a bit stressed, naturally, but my mood is generally okay."),
    ("Doctor", "Are you having any trouble with your memory or concentrating on tasks?"),
    ("Patient", "No more than usual. I'm just busy."),
    ("Doctor", "Have you ever had any surgeries on your lungs or heart?"),
    ("Patient", "No surgeries other than my appendix when I was twelve."),
    ("Doctor", "Do you use any tobacco products, including vaping?"),
    ("Patient", "I quit smoking ten years ago. Never vaped."),
    ("Doctor", "How much alcohol do you consume in a typical week?"),
    ("Patient", "Maybe two or three beers on the weekend, that's about it."),
    ("Doctor", "Have you ever used any recreational drugs?"),
    ("Patient", "No, never."),
    ("Doctor", "Any history of blood clots or deep vein thrombosis in your family?"),
    ("Patient", "My aunt had a clot in her leg after a long flight once."),
    ("Doctor", "Are you up to date on your vaccinations, including the flu shot?"),
    ("Patient", "Yes, I got my flu shot last October."),
    ("Doctor", "Any history of glaucoma or cataracts?"),
    ("Patient", "No, my eyes are healthy."),
    ("Doctor", "Do you wear glasses or contacts?"),
    ("Patient", "I have some reading glasses, but that's it."),
    ("Doctor", "Any history of hearing loss or ringing in your ears?"),
    ("Patient", "Maybe a little ringing if I've been at a loud concert, but it goes away."),
    ("Doctor", "How is your skin generally? Do you use sunscreen regularly?"),
    ("Patient", "I try to if I'm going to be outside for a long time."),
    ("Doctor", "Any history of skin cancer, like basal cell or melanoma?"),
    ("Patient", "None for me, fortunately."),
    ("Doctor", "How about your family? Any significant heart disease or early strokes?"),
    ("Patient", "My grandfather had a heart attack in his late seventies."),
    ("Doctor", "Are you currently seeing any other specialists besides me?"),
    ("Patient", "Just my primary care doctor for my annual checkup."),
    ("Doctor", "Have you had a recent COVID-19 infection or any lingering symptoms?"),
    ("Patient", "I had it last year, but I felt better after about a week."),
    ("Doctor", "Any history of depression or anxiety that required medication?"),
    ("Patient", "No, I've been pretty stable."),
    ("Doctor", "Do you have any pets at home? Any seasonal allergies to them?"),
    ("Patient", "We have a golden retriever. I'm not allergic, thankfully."),
    ("Doctor", "What kind of work do you do? Is it physically demanding?"),
    ("Patient", "I'm a software engineer, so I sit at a desk most of the day."),
    ("Doctor", "Do you find yourself eating late at night or skipping meals often?"),
    ("Patient", "I usually have a late snack, but I try to eat three meals."),
    ("Doctor", "How has your weight been over the last five years? Stable?"),
    ("Patient", "I've gained about ten pounds, but I'm trying to lose it.")
]

async def synthesize_case(case_id, data):
    print(f"[*] Synthesizing {case_id}: {data['disease']}...")
    
    target_mins = data.get("target_mins") or random.uniform(7.0, 13.0)
    base_script = data["script"]
    
    # Intelligently expand if too short
    # Estimate: each pair is ~18s. 
    # To hit 7-13 mins (avg 10), we need ~35-40 pairs. 
    script = base_script.copy()
    
    # We want to insert around 30-40 unique ROS/History items to reach 10+ minutes
    if len(script) < 45:
        # Increase filler to hit the 10-minute sweet spot
        filler_count = random.randint(30, 45)
        filler = random.sample(ROS_POOL, min(len(ROS_POOL), filler_count))
        # Insert filler after the initial HPI
        insert_idx = min(len(script), 8)
        for f in filler:
            script.insert(insert_idx, f)
            insert_idx += 1

    combined_audio = AudioSegment.empty()
    raw_text = ""
    chunk_idx = 0
    
    for speaker, text in script:
        voice = VOICE_DOCTOR if speaker == "Doctor" else VOICE_PATIENT
        # Dynamic rate for realism
        rate = random.choice(["-8%", "-3%", "+0%", "+5%"])
        
        temp_file = f"temp_{case_id}_{chunk_idx}.mp3"
        
        # Phase 10: Robustness Enhancement
        # Retry logic for edge-tts to handle connection timeouts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                await communicate.save(temp_file)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[!] Critical failure on {case_id} chunk {chunk_idx}: {e}")
                    raise
                await asyncio.sleep(2 * (attempt + 1))
        
        segment = AudioSegment.from_mp3(temp_file)
        
        # Phase 10: Acoustic Augmentation
        # Layer subtle ambient white noise to simulate real-world clinic background
        # This forces Whisper to be more robust to non-ideal conditions.
        white_noise = AudioSegment.silent(duration=len(segment)).set_frame_rate(segment.frame_rate)
        # We simulate noise by just taking a silent segment and lowering the 'silence' bar? 
        # Actually pydub doesn't have a native white_noise generator in the base AudioSegment easily.
        # But we can add a very quiet 'static' by using a pre-generated noise or simple hack.
        # Let's just use a very low volume overlay of a slightly randomized segment or just leave it for now if pydub is limited.
        # Better: inject a small amount of volume-reduced white noise.
        try:
            from pydub.generators import WhiteNoise
            noise = WhiteNoise().to_audio_segment(duration=len(segment), volume=-45) # Very subtle
            segment = segment.overlay(noise)
        except:
            pass # Fallback if pydub.generators is missing

        # Save chunk
        chunk_name = f"{case_id}_chunk_{chunk_idx:03d}"
        chunk_mp3_path = TRAIN_DIR / f"{chunk_name}.mp3"
        chunk_json_path = TRAIN_DIR / f"{chunk_name}.json"
        segment.export(chunk_mp3_path, format="mp3")
        
        with open(chunk_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "audio_file": str(chunk_mp3_path),
                "raw_transcript": text,
                "final_corrected_note": text,
                "was_edited": True
            }, f, indent=4)
        
        chunk_idx += 1
        combined_audio += segment
        combined_audio += AudioSegment.silent(duration=random.randint(1200, 2200)) # Natural pauses
        
        os.remove(temp_file)
        raw_text += f"{speaker}: {text}\n"

    final_path = OUTPUT_DIR / f"{case_id}.mp3"
    combined_audio.export(final_path, format="mp3")
    
    duration_mins = len(combined_audio) / 60000.0
    print(f"[+] Finalized {case_id} ({duration_mins:.2f} mins) with {chunk_idx} unique blocks.")
    
    # Save training manifest for the full session
    with open(Path("data/training_corpus") / f"{case_id}.json", "w", encoding="utf-8") as f:
        json.dump({
            "audio_file": str(final_path),
            "raw_transcript": raw_text.strip(),
            "corrected_note": "Hand-crafted clinical encounter for " + data['disease'],
            "was_edited": False
        }, f, indent=4)

async def main():
    if not SCRIPTS_FILE.exists():
        print(f"Error: {SCRIPTS_FILE} not found.")
        return
        
    with open(SCRIPTS_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)
        
    # Process GAS0008 to GAS0027
    tasks = []
    # We'll run them sequentially to avoid edge-tts rate limits or system lag
    for case_id in sorted(all_data.keys()):
        await synthesize_case(case_id, all_data[case_id])

if __name__ == "__main__":
    asyncio.run(main())
