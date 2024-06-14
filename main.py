from typing import Union

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

import os

from fastapi.responses import JSONResponse

app = FastAPI()

load_dotenv()

s3_client = boto3.client(
    's3',
    region_name='nyc3',
    endpoint_url=os.getenv("DIGITAL_OCEAN_ORIGIN"),
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
            ExpiresIn=60
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
    uvicorn.run(app, host="0.0.0.0", port=8000)