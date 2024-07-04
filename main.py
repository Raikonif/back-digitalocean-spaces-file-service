import logging

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from dotenv import load_dotenv

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

session = boto3.session.Session()
s3_client = session.client(
    's3',
    region_name='nyc3',  # Reemplaza con tu región
    endpoint_url=os.getenv("DIGITAL_OCEAN_ORIGIN"),  # Reemplaza con tu endpoint
    aws_access_key_id=os.getenv("DIGITAL_OCEAN_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("DIGITAL_OCEAN_SECRET_KEY")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "127.0.0.1:5173", "syspdfsur.vercel.app"],  # Reemplaza con el origen de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        if file is None:
            raise HTTPException(status_code=400, detail="No file uploaded")

        file_bytes = await file.read()
        if file_bytes is None:
            raise HTTPException(status_code=400, detail="File content is None")

        filename = file.filename
        s3_client.put_object(
            Bucket=os.getenv("DIGITAL_OCEAN_BUCKET"),
            Key=filename,
            Body=file_bytes,
            ACL='public-read',
            ContentType=file.content_type,
        )
        file_url = f"{os.getenv('DIGITAL_OCEAN_ORIGIN')}/{os.getenv('DIGITAL_OCEAN_BUCKET')}/{filename}"
        logger.info(f"File URL: {file_url}")
        # return {"imageUrl": file_url}
        return JSONResponse(content={"file_url": file_url})

    except NoCredentialsError as e:
        logger.error(f"Credentials not provided or incorrect: {e}")
        raise HTTPException(status_code=401, detail="Could not authenticate with the provided credentials")

    except PartialCredentialsError as e:
        logger.error(f"Partial credentials provided: {e}")
        raise HTTPException(status_code=500, detail="Incomplete credentials")

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/delete/")
async def delete_image(filename: str = Query(...)):
    try:
        s3_client.delete_object(
            Bucket=os.getenv("DIGITAL_OCEAN_BUCKET"),
            Key=filename
        )
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting file")


@app.get("/generate-presigned-url")
async def generate_presigned_url(bucket_name: str = Query(...), key: str = Query(...)):
    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': key,
                'ACL': 'public-read'
            },
            ExpiresIn=120
        )
        return JSONResponse(content={"url": url})
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=500, detail="Credentials incomplete")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
