import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.two_pass_summarizer import TwoPassSummarizer
from app.config import SummarizerConfig

logging.basicConfig(level=logging.INFO)

TRANSCRIPT = """what brings you in today i've just been feeling like very nauseated for it feels like all the time right now when did this start it's been over a week maybe not quite two weeks but like around then yeah maybe like nine days and um is it do you always have the sensation of nausea or is it related or does it come and go oh i think it's like worse when I am smelling something really bad, and it's worse in the morning. But I feel like it's always kind of there. I see okay. Um have you had any vomiting? Uh yeah like um yeah like a lot of days I'll throw up like once or twice. And this has all been over the past week week two weeks or so? Yeah. Okay um any other symptoms that you have? Oh no just well like I feel like I've, I've had to pee a lot more. Um, but I don't, I don't think that's like related. I think maybe I have just been drinking a lot of water. So yeah. How often do you have to pee? Oh, like I feel like every couple hours right now. Okay. So say every two hours, every hour, every five hours, probably every, probably every like two, maybe, maybe every hour I get certain times in a day. Do you wake up at night to pee? Oh like it doesn't wake me up but it's like I wake up because I hear something then I'll be like oh I think I should probably go to the bathroom. Yeah do you feel like you have control over when you are going to bathroom or is it difficult for you to hold it in? Oh I can control it it's just like uncomfortable right i see i see so um you have urinary frequency but do you do you feel like uh so you said that you can control it you don't you don't feel like you need to run to the bathroom or you'll pee in your pants no i don't feel like that okay do you have any pain when you're peeing no no okay all right um do you feel like you've been more thirsty recently why do you feel you've been drinking more more water i think i think just cause like i was getting i was like throwing up so like i feel like i was a little dehydrated um i see okay um have you other than the nausea and vomiting have you had any other stomach related issues any belly pain or changes in your bowel movements uh no i don't think so well my stomach has been like it feels like a little crampy. I thought that maybe it could be my period, but like I'm not on my period. When did you last have your period? Oh well, let me think. Um, like six weeks ago. I guess that would be, I don't know. I don't really like keep track. Okay, okay. Do you know if you get your periods regularly or are your periods irregular? I think they are, I think they're usually pretty regular but i don't i don't like i don't calculated light to the day true yeah is it normal for you to go six weeks without a period oh come to think of it i don't i don't think so all right um okay uh have you i'll just ask you a couple more questions about your symptoms so i know that you've been nauseous and have vomited a couple of times in the past two weeks And, you have had some cramps in your belly. Have you had any flu-like symptoms? No Nothing like that? I don't think so Any headaches? Uh no Any fevers? No Muscle aches? Uh no Okay, um, have you, have you had a cough at all? Oh no Okay, and have you noticed any blood in your stools? No. Have you, you haven't had any palpitations or chest pain or anything of that sort? No. Alright um can you tell me about your past medical history, any medical issues, medical conditions that you have? Ah nothing, nothing really. Okay. Have you, um been taking any medications? No I mean, I've been taking like like I've been chewing like those ginger things that are supposed to help with nausea but they weren't really helpful i see any allergies so just like nickel like in jewelry if i wear not real jewelry it'll give me a rash but it's not food or like or medications or anything um and uh a couple of questions about your social history who do you currently live with um like i i just i live with one roommate Um and, do you currently smoke? No Alright, you don't smoke, okay Have you, do you consume alcohol? Ah no, very rarely because I always get a headache Okay, when was the last drink that you had? Oh gosh, like like a month ago probably Okay, um, and you consume any illicit drugs? No, no Alright, are you currently sexually active? yeah just like with my boyfriend and do you use protection while having sex yeah we we just use condoms i used to be on birth control but it always made me feel like kind of sick so i don't use that anymore mitch um i see okay uh and um let's see family history do you do you have any medical conditions that run in your family Ah, like I don't. I don't think so. I guess my dad-my dad has like high blood pressure, yeah. I don't think there's anything else. Alright, alright, well, thank you so much for spending time with me today. I think I have gathered all the information that I would've liked. I will go talk to my attending, we'll come back and maybe ask a couple more questions and then share the plan with you. Okay, thank you. You're welcome."""

def test_summarization():
    config = SummarizerConfig(
        base_url="http://localhost:11434",
        model="llama3.1",
        timeout_s=600,
        max_tokens=2048,
        use_self_correction=False
    )
    # Patch context window if not in class
    config.context_window = 8192
    
    summarizer = TwoPassSummarizer(config)
    print("Starting Summarization Test V3...")
    
    # Run the summary
    summary_text = summarizer.summarize_text(TRANSCRIPT)
    
    print("\n" + "="*50)
    print("FINAL CLINICAL NOTE:")
    print("="*50)
    print(summary_text)
    print("="*50)

if __name__ == "__main__":
    test_summarization()
