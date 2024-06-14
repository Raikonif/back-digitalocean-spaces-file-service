import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from dotenv import load_dotenv

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()
s3_client = boto3.client(
    's3',
    region_name='nyc3',  # Reemplaza con tu región
    endpoint_url=os.getenv("DIGITAL_OCEAN_ORIGIN"),  # Reemplaza con tu endpoint
    aws_access_key_id=os.getenv("DIGITAL_OCEAN_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("DIGITAL_OCEAN_SECRET_KEY")
)


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
        raise HTTPException(status_code=500, detail="Credenciales no encontradas")
    except PartialCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciales incompletas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
