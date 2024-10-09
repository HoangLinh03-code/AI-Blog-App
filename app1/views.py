from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai
import yt_dlp
import requests
from .models import BlogPost
# Create your views here.
@login_required
def index(request):
    return render(request, 'home.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error':'Invalid data sent'})
        
        #get yt title
        title = yt_title(yt_link)
        #get transcipt
        transcipts = get_transcript(yt_link)
        if not transcipts:
            return JsonResponse({'error': 'Failed to get transcipts'})
        #use OpenAI to generate blog
        blog_content = generate_blog_from_trans(transcipts)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'})
        # #Save blog article to database
        new_blog_article = BlogPost.objects.create(
            user = request.user,
            you_tube_title = title,
            you_tube_link = yt_link,
            generate = blog_content,
        )
        new_blog_article.save()
        # #return blog article as a response
        return JsonResponse({'content':blog_content})
    else:
        return JsonResponse({'error':'Invalid request method'})
    
def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title    

def generate_blog_from_trans(transcript):
    openai.api_key = "sk-ijajss53fK5rJL3ZleHIBZ21WHBoaoDDr3mvfMAUi6T3BlbkFJdHv2YlHcArNhD-X478toJ42Vyaf_pIjdHSUI4J_ZoA"
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article:\n\n{transcript}\n\nArticle:"
    # try:
    #     response = openai.Completion.create(
    #         model="gpt-4o-mini",
    #         prompt=prompt,
    #         max_tokens=1000
    #     )
    #     return response.choices[0].text.strip()
    # except Exception as e:
    #     print(f"Error with OpenAI API: {str(e)}")
    #     return None  
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message['content'].strip()
    except openai.error.RateLimitError:
        print("Rate limit exceeded. Please try again later.")
        return None
    except openai.error.InvalidRequestError as e:
        if "quota" in str(e):
            print("You have exceeded your current quota. Please check your plan and billing details.")
        else:
            print(f"Invalid request: {e}")
        return None
    except Exception as e:
        print(f"Error with OpenAI API: {str(e)}")
        return None 
    

def download_audio(link):
    media_root = settings.MEDIA_ROOT  # Use MEDIA_ROOT from Django settings
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(media_root, '%(title)s.%(ext)s'),  # Save to media folder
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        # Return the full path to the downloaded file (in MEDIA_ROOT)
        return os.path.join(media_root, ydl.prepare_filename(info).replace('.webm', '.mp3'))

def get_transcript(link):
    try:
        # Step 1: Define the expected audio file path in the MEDIA_ROOT directory
        audio_file_name = os.path.basename(link) + '.mp3'  # Assuming you're saving as .mp3
        media_audio_file = os.path.join(settings.MEDIA_ROOT, audio_file_name)

        # Step 2: Check if the audio file already exists
        if os.path.exists(media_audio_file):
            print(f"Audio file already exists: {media_audio_file}")
        else:
            # Download the audio file from YouTube into the 'media' directory
            media_audio_file = download_audio(link)  # This function should now return the saved path
            print(f"Audio file downloaded: {media_audio_file}")

        # Step 3: Transcribe the audio file using AssemblyAI
        aai.settings.api_key = "fd9d1155e9eb416fa181a20fd008b0db"
        transcriber = aai.Transcriber()
        transcripts = transcriber.transcribe(media_audio_file)
        
        if transcripts.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription error: {transcripts.error}")
        
        return transcripts.text

    except Exception as e:
        print(f"Error with AssemblyAI API: {str(e)}")
        return None

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username= username, password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'Login.html', {'error_message': error_message})
    return render(request, 'Login.html')
def signup(request):
    if request.method == 'POST' :
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeat_password = request.POST['repeatPassword']
        if password == repeat_password:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                login(request, user)
                return redirect('/')
            except IntegrityError: 
                error_message = 'Username or email already exists'
                return render(request, 'Signup.html', {'error_message': error_message})
            except Exception as e:
                error_message = f'Error creating account: {e}'
                return render(request, 'Signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'Signup.html', {'error_message': error_message})
    
    return render(request, 'Signup.html')
def allblog(request):
    return render(request, 'all_blog.html')
def blog(request):
    return render(request, 'Blog-detail.html')
def logout_user(request):
    logout(request)
    return redirect('/')
def blog_list(request):
    blog_article = BlogPost.objects.filter(user = request.user)
    return render(request, 'all_blog.html', {'blog_articles':blog_article})

def blog_detail(request, pk):
    blog_articles_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_articles_detail:
        return render(request, 'Blog-detail.html', {'blog_articles_detail': blog_articles_detail})
    else:
        return redirect('/')