# Mock Commerce Backend

This is a disposable, in-memory FastAPI backend for local LangGraph experiments.
Data resets whenever the server restarts and can also be restored with `POST /reset`.

## Run locally

Using Python 3.10 or newer:

```powershell
cd backend-mock
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend-mock:app --reload
```

Open the Swagger UI at <http://127.0.0.1:8000/docs>.

The sample order IDs are `101` through `105`. For example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/customers/1/orders
Invoke-RestMethod http://127.0.0.1:8000/orders/101/cancellation-eligibility
Invoke-RestMethod -Method Post http://127.0.0.1:8000/orders/101/cancel
Invoke-RestMethod -Method Post http://127.0.0.1:8000/reset
```
