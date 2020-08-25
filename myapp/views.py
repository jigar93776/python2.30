from django.shortcuts import render,redirect
from .models import Contact,User,Book,Cart,Wishlist,Transaction
from django.conf import settings
import random
from django.core.mail import send_mail
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

def initiate_payment(request):
    if request.method == "GET":
        return render(request, 'myapp/pay.html')
    try:
        
        amount = int(request.POST['amount'])
        
    except:
        return render(request, 'myapp/pay.html', context={'error': 'Wrong Accound Details or amount'})
    user=User.objects.get(email=request.session['email'])
    transaction = Transaction.objects.create(made_by=user, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(user.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://localhost:8000/callback'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'myapp/redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
        return render(request, 'myapp/callback.html', context=received_data)

def index(request):
	return render(request,'myapp/index.html')

def python(request):
	books=Book.objects.filter(book_category='python')
	return render(request,'myapp/book.html',{'books':books})

def java(request):
	books=Book.objects.filter(book_category='java')
	return render(request,'myapp/book.html',{'books':books})

def php(request):
	books=Book.objects.filter(book_category='php')
	return render(request,'myapp/book.html',{'books':books})

def contact(request):
	if request.method=="POST":
		name=request.POST['name']
		email=request.POST['email']
		mobile=request.POST['mobile']
		remarks=request.POST['remarks']
		Contact.objects.create(name=name,email=email,mobile=mobile,remarks=remarks)
		#msg="Contact Saved Successfully"
		#contacts=Contact.objects.all().order_by("-name")
		#return render(request, 'myapp/contact.html',{'msg':msg,'contacts':contacts})
		return redirect("contact")
	else:
		contacts=Contact.objects.all().order_by("-name")
		return render(request,'myapp/contact.html',{'contacts':contacts})

def signup(request):
	if request.method=="POST":
		user=User()
		user.usertype=request.POST['usertype']
		user.fname=request.POST["fname"]
		user.lname=request.POST["lname"]
		user.email=request.POST["email"]
		user.mobile=request.POST["mobile"]
		user.password=request.POST["password"]
		user.cpassword=request.POST["cpassword"]
		user.user_image=request.FILES['userimage']

		a=User.objects.filter(email=user.email)
		if a:
			msg="Email Already Exist"
			return render(request,'myapp/signup.html',{'msg':msg})
		elif user.password==user.cpassword:
			User.objects.create(first_name=user.fname,last_name=user.lname,email=user.email,mobile=user.mobile,password=user.password,cpassword=user.cpassword,usertype=user.usertype,user_image=user.user_image)
			rec=[user.email,]
			subject="OTP For Registration"
			otp=random.randint(1000,9999)
			message="Your OTP For Successfull Registration Is "+str(otp)
			email_from=settings.EMAIL_HOST_USER
			send_mail(subject,message,email_from,rec)
			return render(request,'myapp/verify_otp.html',{'otp':otp,'email':user.email})
		else:
			msg="Password & Confirm Password Does Not Matched"
			return render(request,'myapp/signup.html',{'msg':msg,'user':user})
	else:
		return render(request,'myapp/signup.html')

def login(request):
	if request.method=="POST":
		email=request.POST['email']
		password=request.POST['password']
		try:
			user=User.objects.get(email=email,password=password)
			print(user.user_image.url)
			if user.status=="active" and user.usertype=="user":
				request.session['fname']=user.first_name
				request.session['email']=user.email
				request.session['userimage']=user.user_image.url
				carts=Cart.objects.filter(user=user)
				wishlists=Wishlist.objects.filter(user=user)
				request.session['mycart']=len(carts)
				request.session['wishlist']=len(wishlists)
				return render(request,'myapp/index.html')
			elif user.status=="active" and user.usertype=="seller":
				request.session['fname']=user.first_name
				request.session['email']=user.email
				request.session['userimage']=user.user_image.url
				print("seller Called")
				return render(request,'myapp/seller_index.html')
			else:
				msg="You still not verified your account.Enter email to get OTP"
				return render(request,'myapp/enter_email.html',{'msg':msg})
		except:
			msg="Email or Password is incorrect"
			return render(request,'myapp/login.html',{'msg':msg})	

	else:
		return render(request,'myapp/login.html')

def verify_otp(request):
	otp=request.POST["otp"]
	email=request.POST["email"]
	u_otp=request.POST["u_otp"]

	if otp==u_otp:
		user=User.objects.get(email=email)
		if user.status=="active":
			return render(request,'myapp/new_password.html',{'email':email})
		else:	
			user.status="active"
			user.save()
			return redirect("login")
	else:
		msg="Entered otp is incorrect. Please enter again."
		return render(request,'myapp/verify_otp.html',{'otp':otp,'email':email,'msg':msg})

def send_otp(request):
	email=request.POST['email']
	try:
		user=User.objects.get(email=email)
		if user:
			rec=[email,]
			subject="OTP For Validation"
			otp=random.randint(1000,9999)
			message="Your OTP For Successfull Registration Is "+str(otp)
			email_from=settings.EMAIL_HOST_USER
			send_mail(subject,message,email_from,rec)
			return render(request,'myapp/verify_otp.html',{'otp':otp,'email':email})
	except:
		msg="Email does not exist."
		return render(request,'myapp/login.html',{'msg':msg})

def logout(request):
	try:
		del request.session['fname']
		del request.session['email']
		del request.session['userimage']
		return render(request,'myapp/login.html')
	except:
		pass

def enter_email(request):
	return render(request,'myapp/enter_email.html')

def forgot_password(request):
	email=request.POST['email']
	password=request.POST['password']
	cpassword=request.POST['cpassword']
	if password==cpassword:
		try:
			user=User.objects.get(email=email)
			user.password=password
			user.cpassword=cpassword
			user.save()
			msg="Password updated successfully"
			return render(request,'myapp/login.html',{'msg':msg})
		except:
			pass
	else:
		msg="Password & Confirm Password Does Not Matched."
		return render(request,'myapp/new_password.html',{'msg':msg,'email':email})

def change_password(request):
	if request.method=="POST":
		user=User.objects.get(email=request.session['email'])
		old_password=request.POST['old_password']
		new_password=request.POST['new_password']
		new_cpassword=request.POST['new_cpassword']

		if user.password!=old_password:
			msg="Old Password Is Incorrect"
			return render(request,'myapp/change_password.html',{'msg':msg})
		elif new_password!=new_cpassword:
			msg="New Password & Confrim New Password Does Not Matched"
			return render(request,'myapp/change_password.html',{'msg':msg})
		else:
			user.password=new_cpassword
			user.cpassword=new_cpassword
			user.save()
			try:
				del request.session['fname']
				del request.session['email']
				msg="Password Changed Successfully. Please Login Again."
				return render(request,'myapp/login.html',{'msg':msg})
			except:
				pass

	return render(request,'myapp/change_password.html')

def add_book(request):
	if request.method=="POST":
		bc=request.POST['book_category']
		bn=request.POST['book_name']
		bp=request.POST['book_price']
		ba=request.POST['book_author']
		bd=request.POST['book_desc']
		bi=request.FILES['book_image']
		bse=request.session['email']
		Book.objects.create(book_category=bc,book_name=bn,book_price=bp,book_author=ba,book_desc=bd,book_image=bi,book_seller_email=bse)
		msg="Book Added Successfully"
		return render(request,'myapp/add_book.html',{'msg':msg})
	else:
		return render(request,'myapp/add_book.html')
def seller_index(request):
	return render(request,'myapp/seller_index.html')

def view_book(request):
	books=Book.objects.filter(book_status="active",book_seller_email=request.session['email'])
	return render(request,'myapp/view_book.html',{'books':books})

def book_detail(request,pk):
	book=Book.objects.get(pk=pk)
	return render(request,'myapp/book_detail.html',{'book':book})
def user_book_detail(request,pk):
	book=Book.objects.get(pk=pk)
	return render(request,'myapp/user_book_detail.html',{'book':book})
def delete_book(request,pk):
	book=Book.objects.get(pk=pk)
	book.book_status="inactive"
	book.save()
	books=Book.objects.filter(book_status="active")
	return render(request,'myapp/view_book.html',{'books':books})

def inactive_books(request):
	books=Book.objects.filter(book_status="inactive")
	return render(request,'myapp/inactive_books.html',{'books':books})

def book_active(request,pk):
	book=Book.objects.get(pk=pk)
	book.book_status="active"
	book.save()
	books=Book.objects.filter(book_status="inactive")
	return render(request,'myapp/inactive_books.html',{'books':books})

def search_book(request):
	search=request.POST['search']
	books=Book.objects.filter(book_seller_email=request.session['email'],book_status="active",book_category__contains=search)
	return render(request,'myapp/view_book.html',{'books':books})

def profile(request):
	if request.method=="POST":
		u=User.objects.get(email=request.session['email'])
		e=request.POST['email']
		user=User.objects.get(email=e)
		f=request.POST['fname']
		l=request.POST['lname']
		m=request.POST['mobile']
		
		try:
			if request.FILES['userimage']:
				ui=request.FILES['userimage']
		except:
			ui=user.user_image
		user.first_name=f
		user.last_name=l
		user.mobile=m
		user.user_image=ui
		user.save()
		request.session['fname']=user.first_name
		request.session['email']=user.email
		request.session['userimage']=user.user_image.url
		msg="Profile Updated Successfully"
		print("User Type : ",u.usertype)
		if u.usertype=="seller":
			data="seller_header.html"
			return render(request,'myapp/profile.html',{'msg':msg,'user':user,'data':data})
		else:
			return render(request,'myapp/profile.html',{'msg':msg,'user':user})
	else:
		user=User.objects.get(email=request.session['email'])

		if user.usertype=="seller":
			data="seller_header.html"
			return render(request,'myapp/profile.html',{'user':user,'data':data})
		else:
			return render(request,'myapp/profile.html',{'user':user})

def add_to_cart(request,pk):
	total_price=0
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(user=user,book=book)
	mycart=Cart.objects.filter(user=user)
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['mycart']=len(carts)
	request.session['wishlist']=len(wishlists)
	for i in mycart:
		total_price=total_price+int(i.book.book_price)
	print("Total Price : ",total_price)
	return render(request,'myapp/mycart.html',{'mycart':mycart,'total_price':total_price})

def mycart(request):
	total_price=0
	user=User.objects.get(email=request.session['email'])
	mycart=Cart.objects.filter(user=user)
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['mycart']=len(carts)
	request.session['wishlist']=len(wishlists)
	for i in mycart:
		total_price=total_price+int(i.book.book_price)
	print("Total Price : ",total_price)
	return render(request,'myapp/mycart.html',{'mycart':mycart,'total_price':total_price})

def remove_cart(request,pk):
	total_price=0
	mycart=Cart.objects.get(pk=pk)
	mycart.delete()
	user=User.objects.get(email=request.session['email'])
	mycart=Cart.objects.filter(user=user)
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['mycart']=len(carts)
	request.session['wishlist']=len(wishlists)

	for i in mycart:
		total_price=total_price+int(i.book.book_price)
	print("Total Price : ",total_price)
	return render(request,'myapp/mycart.html',{'mycart':mycart,'total_price':total_price})

def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=Wishlist.objects.filter(user=user)
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['mycart']=len(carts)
	request.session['wishlist']=len(wishlists)
	return render(request,'myapp/wishlist.html',{'wishlists':wishlists})

def add_to_wishlist(request,pk):
	cart=Cart.objects.get(pk=pk)
	books=Wishlist.objects.filter(user=cart.user,book=cart.book)
	if books:
		msg="This book is already available in wishlist"
		user=User.objects.get(email=request.session['email'])
		wishlists=Wishlist.objects.filter(user=user)
		return render(request,'myapp/wishlist.html',{'wishlists':wishlists,'msg':msg})		
	else:
		Wishlist.objects.create(user=cart.user,book=cart.book)
		cart.delete()
		user=User.objects.get(email=request.session['email'])
		carts=Cart.objects.filter(user=user)
		wishlists=Wishlist.objects.filter(user=user)
		request.session['mycart']=len(carts)
		request.session['wishlist']=len(wishlists)
		return render(request,'myapp/wishlist.html',{'wishlists':wishlists})	

def wishlist_to_cart(request,pk):
	wishlist=Wishlist.objects.get(pk=pk)
	Cart.objects.create(user=wishlist.user,book=wishlist.book)
	wishlist.delete()
	user=User.objects.get(email=request.session['email'])
	mycart=Cart.objects.filter(user=user)
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['mycart']=len(carts)
	request.session['wishlist']=len(wishlists)
	return render(request,'myapp/mycart.html',{'mycart':mycart})