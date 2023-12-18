from fastapi import FastAPI, status, Depends, UploadFile, HTTPException, File, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from . import models
from . import schemas
from .database import engine, get_db, mongodb_db
from bson.binary import Binary
from passlib.context import CryptContext

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)


@app.post(
    "/user/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserResponse,
)
def create_user(
    name:str = Form(...),
    email:str =  Form(...),
    password:str = Form(...),
    phone_number:str = Form(...),
    profile_pic: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = schemas.UserCreate(name=name, email=email, password=password, phone_number=phone_number)
    try:
        existing_user = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_user: 
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        hashed_pwd = pwd_context.hash(user.password)
        user.password = hashed_pwd
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        if profile_pic:

            allowed_content_types = ["image/jpeg", "image/png"]
            if profile_pic.content_type not in allowed_content_types:
                raise HTTPException(status_code=400, detail="Invalid file type")

            file_content = profile_pic.file.read()
            profile_pics_collection = mongodb_db["profile_pics"]
            result = profile_pics_collection.insert_one(
                {"user_id": new_user.id, "file_data": Binary(file_content)}
            )
        user_response = schemas.UserResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            phone_number=new_user.phone_number,
            created_at=new_user.created_at
        )

        return user_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == id).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        
        profile_pics_collection = mongodb_db["profile_pics"]
        result = profile_pics_collection.find({"user_id": user.id})

        
        return schemas.UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            created_at=user.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/user/profile-pic/{user_id}")
def get_profile_pics(user_id: int):
    try:
        profile_pics_collection = mongodb_db["profile_pics"]
        result = profile_pics_collection.find({"user_id": user_id})

        if not result:
            raise HTTPException(status_code=404, detail="No images found for the given user_id")

        profile_pic = result[0]["file_data"]
        return StreamingResponse(io.BytesIO(profile_pic), media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
