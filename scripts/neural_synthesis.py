import asyncio
import edge_tts
import re
import os
from pathlib import Path

VOICES = {
    "D": "en-US-GuyNeural",
    "P": "en-AU-NatashaNeural"
}

async def synthesize_file(txt_path: Path):
    mp3_path = txt_path.with_suffix(".mp3")
    print(f"Neural synthesizing {txt_path.name}...")
    
    content = txt_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    temp_files = []
    temp_dir = Path("tmp_audio")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        for i, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            # Determine speaker
            speaker = "D"
            if line.startswith("P:"): speaker = "P"
            elif line.startswith("D:"): speaker = "D"
            
            # Clean text
            clean_line = re.sub(r'^[DP]:\s*', '', line)
            if not clean_line.strip(): continue
            
            temp_file = temp_dir / f"line_{i:04d}.mp3"
            communicate = edge_tts.Communicate(clean_line, VOICES[speaker])
            await communicate.save(str(temp_file))
            temp_files.append(temp_file)
            
        # Concatenate using ffmpeg
        if not temp_files: return
        
        list_file = temp_dir / "list.txt"
        with open(list_file, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf.resolve()}'\n")
        
        # Use ffmpeg to join without re-encoding if possible
        cmd = f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{mp3_path}"'
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        
        print(f"  [SUCCESS] Created {mp3_path.name}")
        
    finally:
        # Cleanup
        for tf in temp_files:
            if tf.exists(): tf.unlink()
        if (temp_dir / "list.txt").exists(): (temp_dir / "list.txt").unlink()

async def main():
    source_dir = Path("data/Clinical_Encounters")
    txt_files = sorted(list(source_dir.glob("GAS*.txt")))
    
    for txt_path in txt_files:
        await synthesize_file(txt_path)

if __name__ == "__main__":
    asyncio.run(main())
