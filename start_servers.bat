start cmd /c "cd .\frontend\ & cd & http-server & pause"
start cmd /c "cd .\backend\.venv\Scripts & activate.bat & cd .. & cd .. & cd & uvicorn main:app --reload & pause"