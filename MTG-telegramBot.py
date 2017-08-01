import json
import requests
import time
import shutil
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from mtgsdk import Card
from mtgsdk import Set
from mtgsdk import Type
from mtgsdk import Supertype
from mtgsdk import Subtype
from mtgsdk import Changelog
import enchant
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract'


Token="YOUR_TOKEN"
Url="https://api.telegram.org/bot"+Token+"/"

def get_url(url):
	response =requests.get(url)
	content=response.content.decode("utf8")
	return content
	
def get_json_from_url(url):
	content=get_url(url)
	js=json.loads(content)
	return js

def get_last_update(updates):
	update_ids=[]
	for update in updates["result"]:
		update_ids.append(int(update["update_id"]))
	return max(update_ids)
def get_updates(offset=None):
	url=Url+"getUpdates?timeout=100"
	if offset:
		url+="&offset="+str(offset)
	js=get_json_from_url(url)
	return js
#This is only for Test
def echo_all(updates):
		for update in updates["result"]:
			try:
				text=update["message"]["text"]
				chat=update["message"]["chat"]["id"]
				username=update["message"]["from"]["username"]
				print('Recived text from '+ str(username))
				print(str(username)+": "+ text)
				if text=="Ciao":
					print('Ciao')
					send_message("Ciao anche a te umano!!", chat)	
				elif text=="\start":
					send_message("Ciao! Inviami una foto di una carta Magic",chat)
				else:
					print('Messaggio pappagallo')
					send_message("Ciao! Inviami una foto di una carta Magic",chat)
				print('\n')
			except Exception as e:
				print (e)


def get_photo(updates):
	for update in updates["result"]:
		Prev_file_size=0
		file_id=''
		chat_id=''
		file_path=''
		try:
			if (update["message"]["photo"]):
				for p in update["message"]["photo"]:
					chat=update["message"]["chat"]["id"]
					file_size=p['file_size']
					if (Prev_file_size<file_size):
						Prev_file_size=file_size
						file_id=p['file_id']
						chat_id=chat
					
				send_message("Grazie della foto! La esamino subito", chat)
				js=get_json_from_url(Url+'getFile?file_id='+file_id)
				#print(js)
				if (len(js["result"])>0):
					try:
						file_path=js["result"]['file_path']
						print(file_path)
					except Exception as e:
						print ('Errore file path: ', e)
									
				
				r=requests.get('https://api.telegram.org/file/bot'+Token+'/'+file_path,stream=True)
				if r.status_code==200:
					with open(file_path,'wb') as f:
						for chunk in r.iter_content(chunk_size=1024): 
							if chunk: # filter out keep-alive new chunks
								f.write(chunk)
								f.flush()
					scanImage(chat_id,file_path)
				else:
					send_message("Mi dispiace ma non sono riuscito a decifrare la foto", chat)
		except Exception as e:
			print ("Errore get photo: "+ str(e))
			
#THIS IS THE FUNCTION I USE IN MY OTHER PROGRAM: https://github.com/Trafitto/Py-MTG-OCR
def scanImage(chat_id, file_path):
	im = Image.open(file_path) #NOTE: WITH 500X500 IMG NO PROBLEM TO READ THE TEXT
	text=''
	enchanceIndex=1 #per fare una prova ho visto che da 12 in poi legge bene
	w,h=im.size
	im.crop((0,0,w,h-250)).save("temp.jpg")
	im2=Image.open("temp.jpg")#.convert('L')
	#im2.show()
	ReadedText=[]
	enhancer = ImageEnhance.Contrast(im2)
	im2 = im2.filter(ImageFilter.MinFilter(3))
	d = enchant.DictWithPWL("en_US","MagicCardName.txt")
	while enchanceIndex<=15: #Testing
		im2 = enhancer.enhance(enchanceIndex)
		im2 = im2.convert('1')
		#im2.show()
		text =(pytesseract.image_to_string(im2,lang='ita'))
		 #print (text)
		print('\nValore contrasto= ',enchanceIndex)
		enchanceIndex+=1
		if text!='' :
			#ReadedText.append(text)
			print ('\n---------Name of Cards---------\n')
			print ('Testo rilevato ',text)
			print ('Testi suggeriti ',d.suggest(text))
			suggerimenti=d.suggest(text)
			if (len(suggerimenti)>0):
				print('Ricerca...')
				for s in suggerimenti:
					if s==text:
						cardToSearch=s
					else:
						cardToSearch=suggerimenti[0] #quella con maggior probabilità di essere esatta
				
				print ('Cerca -> ',cardToSearch)
				cards=Card.where(name=cardToSearch).all()
				if (len(cards)>0):
					#for c in cards:
					print(cards[0].name,' ',cards[0].cmc ,cards[0].colors)
					send_message(str(cards[0].name)+" "+str(cards[0].cmc)+" "+str(cards[0].colors), chat_id)
					break
				else:
					cardsITA=Card.where(language="Italian").where(name=cardToSearch).all()
					if (len(cardsITA)>0):
						#for c in cardsITA:
						print(cardsITA[0].name,' ',' costo= ',cardsITA[0].cmc ,' colore= ', cardsITA[0].colors)
						send_message(str(cardsITA[0].name)+" "+str(cardsITA[0].cmc)+" "+str(cardsITA[0].colors), chat_id)
						break
	send_message("Mi dispiace ma non sono riuscito a decifrare la foto", chat_id)
			
def get_last_chat(updates):
	num_updates=len(updates["result"])
	last_update=num_updates-1
	text=updates["result"][last_update]["message"]["text"]
	chat_id=updates["result"][last_update]["message"]["chat"]["id"]
	return (text,chat_id)
	
def send_message(text,chat_id):
	url=Url+"sendMessage?text={}&chat_id={}".format(text,chat_id)
	get_url(url)
	
#text, chat=get_last_chat(get_updates())
#send_message("Nulla spippolo col python",chat)
try:
	last_update_id=None
	print('Avvio')
	while True:
			updates=get_updates(last_update_id)
			if len(updates["result"])>0:
				last_update_id=get_last_update(updates)+1
				echo_all(updates)
				get_photo(updates)
			time.sleep(0.5)
except KeyboardInterrupt:
    print ('^C received, shutting down the bot')
   
   