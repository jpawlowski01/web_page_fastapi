from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from celery import Celery
from fastapi.staticfiles import StaticFiles


#zadanie
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATABASE_URL = "sqlite:///./shopping_list.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

metadata = MetaData()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

Base.metadata.create_all(bind=engine)

celery = Celery(__name__, broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

@celery.task
def add_product_to_db(name: str):
    db = SessionLocal()
    new_product = Product(name=name)
    db.add(new_product)
    db.commit()
    db.close()

@app.get("/")
async def read_items(request: Request):
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "products": products})

@app.post("/")
async def add_product(name: str = Form(...)):
    db = SessionLocal()
    new_product = Product(name=name)
    db.add(new_product)
    db.commit()
    db.close()
    return RedirectResponse("/", status_code=303)

@app.get("/async")
async def read_items_async(request: Request):
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return templates.TemplateResponse("async_index.html", {"request": request, "products": products})

@app.post("/async")
async def add_product_async(name: str = Form(...)):
    add_product_to_db.delay(name)
    return RedirectResponse("/async", status_code=303)

@app.get("/delete/{product_id}")
async def delete_product(product_id: int):
    db = SessionLocal()
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()
    db.close()
    return RedirectResponse("/", status_code=303)

@app.get("/delete_async/{product_id}")
async def delete_product_async(product_id: int):
    db = SessionLocal()
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()
    db.close()
    return RedirectResponse("/async", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
