from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(AsyncAttrs, DeclarativeBase):
    pass


class PropertyType(enum.Enum):
    LIST = "list"
    INT = "int"


class PropertyValue(Base):
    __tablename__ = "property_values"

    uid = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    property_uid = Column(String, ForeignKey("properties.uid"), nullable=False)

    property = relationship("Property", back_populates="values")


class Property(Base):
    __tablename__ = "properties"

    uid = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(PropertyType), nullable=False)

    values = relationship("PropertyValue", back_populates="property", cascade="all, delete-orphan")
    product_properties = relationship("ProductProperty", back_populates="property")


class ProductProperty(Base):
    __tablename__ = "product_properties"

    id = Column(Integer, primary_key=True)
    product_uid = Column(String, ForeignKey("products.uid"), nullable=False)
    property_uid = Column(String, ForeignKey("properties.uid"), nullable=False)
    value_uid = Column(String, ForeignKey("property_values.uid"), nullable=True)
    int_value = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="properties")
    property = relationship("Property", back_populates="product_properties")
    value = relationship("PropertyValue")


class Product(Base):
    __tablename__ = "products"

    uid = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    properties = relationship("ProductProperty", back_populates="product", cascade="all, delete-orphan")