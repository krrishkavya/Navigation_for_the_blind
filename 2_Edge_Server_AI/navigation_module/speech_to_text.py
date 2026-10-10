import speech_recognition as sr

def get_voice_command():
    """
    Activates the microphone, listens for a user command, 
    and converts the speech to a text string.
    """
    recognizer = sr.Recognizer()
    
    # Use the default laptop microphone
    with sr.Microphone() as source:
        print("\n🎤 Adjusting for background noise... Please wait.")
        # This helps the mic understand what is background noise vs your voice
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("🟢 Listening! Please say your destination now...")
        try:
            # Listen to the user (stops listening automatically when they stop talking)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            # Use Google's free public Speech-to-Text API
            text = recognizer.recognize_google(audio)
            
            print(f"✅ I heard: '{text}'")
            return text
            
        except sr.WaitTimeoutError:
            print("❌ Timeout: You didn't say anything.")
            return None
        except sr.UnknownValueError:
            print("❌ Sorry, I could not understand the audio. Please speak clearly.")
            return None
        except sr.RequestError as e:
            print(f"❌ Network Error: Could not connect to Google Speech service; {e}")
            return None

if __name__ == "__main__":
    # --- LOCAL TESTING BLOCK ---
    print("--- Testing Speech-to-Text Module ---")
    destination = get_voice_command()
    
    if destination:
        print(f"\n🎉 Test Successful! The OSRM routing module will now search for: [{destination}]")
    else:
        print("\n⚠️ Test Failed. Please try running it again.")
