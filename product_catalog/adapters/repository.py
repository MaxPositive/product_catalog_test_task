from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import joinedload
from typing import Any, Optional

from product_catalog.domain.dto import ProductCreate, PropertyCreate
from product_catalog.domain.models import Product, ProductProperty, Property, PropertyType, PropertyValue


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 10,
        name: Optional[str] = None,
        sort: Optional[str] = "uid",
        property_filters: Optional[dict[str, list[str] | dict[str, int]]] = None
    ) -> tuple[list[Product], int]:
        query = (
            select(Product)
            .options(joinedload(Product.properties).joinedload(ProductProperty.property))
            .options(joinedload(Product.properties).joinedload(ProductProperty.value))
        )

        if name:
            query = query.where(Product.name.ilike(f"%{name}%"))

        if property_filters:
            for prop_uid, values in property_filters.items():
                subquery = (
                    select(ProductProperty.product_uid)
                    .where(ProductProperty.property_uid == prop_uid)
                )
                if isinstance(values, list):
                    subquery = subquery.where(ProductProperty.value_uid.in_(values))
                elif isinstance(values, dict):
                    if "from" in values:
                        subquery = subquery.where(ProductProperty.int_value >= values["from"])
                    if "to" in values:
                        subquery = subquery.where(ProductProperty.int_value <= values["to"])
                query = query.where(Product.uid.in_(subquery))

        if sort == "name":
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.uid.asc())

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_query)).scalar()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        products = result.unique().scalars().all()

        return products, total_count

    async def get_filter_stats(
        self,
        name: Optional[str] = None,
        property_filters: Optional[dict[str, list[str] | dict[str, int]]] = None
    ) -> dict[str, Any]:

        base_query = select(Product.uid)
        if name:
            base_query = base_query.where(Product.name.ilike(f"%{name}%"))

        if property_filters:
            for prop_uid, filter_data in property_filters.items():
                subquery = (
                    select(ProductProperty.product_uid)
                    .where(ProductProperty.property_uid == prop_uid)
                )
                if isinstance(filter_data, list):
                    subquery = subquery.where(ProductProperty.value_uid.in_(filter_data))
                elif isinstance(filter_data, dict):
                    if "from" in filter_data:
                        subquery = subquery.where(ProductProperty.int_value >= filter_data["from"])
                    if "to" in filter_data:
                        subquery = subquery.where(ProductProperty.int_value <= filter_data["to"])
                base_query = base_query.where(Product.uid.in_(subquery))

        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = (await self.db.execute(count_query)).scalar()

        stats = {"count": total_count}

        prop_query = select(Property).where(Property.type == PropertyType.LIST)
        list_properties = (await self.db.execute(prop_query)).scalars().all()
        for prop in list_properties:
            value_counts = {}
            value_query = (
                select(ProductProperty.value_uid, func.count(ProductProperty.id))
                .join(Product, ProductProperty.product_uid == Product.uid)
                .where(ProductProperty.property_uid == prop.uid)
                .where(Product.uid.in_(base_query.subquery()))
                .group_by(ProductProperty.value_uid)
            )
            result = await self.db.execute(value_query)
            for value_uid, count in result:
                if value_uid:
                    value_counts[value_uid] = count
            if value_counts:
                stats[prop.uid] = value_counts

        int_prop_query = select(Property).where(Property.type == PropertyType.INT)
        int_properties = (await self.db.execute(int_prop_query)).scalars().all()
        for prop in int_properties:
            int_stats = {}
            min_max_query = (
                select(func.min(ProductProperty.int_value), func.max(ProductProperty.int_value))
                .join(Product, ProductProperty.product_uid == Product.uid)
                .where(ProductProperty.property_uid == prop.uid)
                .where(Product.uid.in_(base_query.subquery()))
            )
            result = await self.db.execute(min_max_query)
            min_val, max_val = result.one()
            if min_val is not None and max_val is not None:
                int_stats["min_value"] = min_val
                int_stats["max_value"] = max_val
                stats[prop.uid] = int_stats

        return stats


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, product_uid: str) -> Product:
        result = await self.db.execute(
            select(Product)
            .options(joinedload(Product.properties).joinedload(ProductProperty.property))
            .options(joinedload(Product.properties).joinedload(ProductProperty.value))
            .where(Product.uid == product_uid)
        )
        product = result.scalars().first()
        if not product:
            raise ValueError(f"Product with UID '{product_uid}' not found")
        return product

    async def add(self, product_data: ProductCreate) -> Product:
        existing_product = await self.db.get(Product, product_data.uid)
        if existing_product:
            raise ValueError(f"Product with UID '{product_data.uid}' already exists")

        for prop in product_data.properties:
            prop_exists = await self.db.get(Property, prop.uid)
            if not prop_exists:
                raise ValueError(f"Property with UID '{prop.uid}' does not exist")

            if prop_exists.type == PropertyType.LIST:
                if prop.value_uid is None:
                    raise ValueError(f"List-type property '{prop.uid}' requires a value_uid")
                value_exists = await self.db.get(PropertyValue, prop.value_uid)
                if not value_exists or value_exists.property_uid != prop.uid:
                    raise ValueError(f"Value UID '{prop.value_uid}' does not exist for property {prop.uid}")
            elif prop_exists.type == PropertyType.INT:
                if prop.value is None:
                    raise ValueError(f"Int-type property '{prop.uid}' requires a value")
                if prop.value_uid is not None:
                    raise ValueError(f"Int-type property '{prop.uid}' should not have a value_uid")

        product = Product(uid=product_data.uid, name=product_data.name)
        self.db.add(product)

        for prop_data in product_data.properties:
            product_prop = ProductProperty(
                product_uid=product_data.uid,
                property_uid=prop_data.uid,
                value_uid=prop_data.value_uid if prop_data.value_uid else None,
                int_value=prop_data.value if prop_data.value is not None else None
            )
            self.db.add(product_prop)

        await self.db.commit()

        result = await self.db.execute(
            select(Product)
            .options(joinedload(Product.properties).joinedload(ProductProperty.property))
            .options(joinedload(Product.properties).joinedload(ProductProperty.value))
            .where(Product.uid == product_data.uid)
        )
        product = result.scalars().first()
        if not product:
            raise ValueError(f"Product '{product_data.uid}' not found after commit")
        return product

    async def delete(self, product_uid: str) -> None:
        product = await self.db.get(Product, product_uid)
        if not product:
            raise ValueError(f"Product with UID '{product_uid}' not found")

        await self.db.execute(delete(Product).where(Product.uid == product_uid))
        await self.db.commit()


class PropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.property_types = [member.value for member in PropertyType]

    async def add(self, property_data: PropertyCreate) -> Property:
        if property_data.type not in self.property_types:
            raise ValueError(f"Invalid property type: '{property_data.type}'. Must be 'list' or 'int'")

        existing_prop = await self.db.get(Property, property_data.uid)
        if existing_prop:
            raise ValueError(f"Property with UID {property_data.uid} already exists")

        if property_data.type == PropertyType.LIST:
            if not property_data.values or len(property_data.values) == 0:
                raise ValueError("List-type property requires at least one value")
        elif property_data.type == PropertyType.INT and property_data.values:
            raise ValueError("Int-type property should not have values")

        property = Property(
            uid=property_data.uid,
            name=property_data.name,
            type=PropertyType[property_data.type.upper()]
        )
        self.db.add(property)

        if property_data.type == PropertyType.LIST:
            for value_data in property_data.values:
                existing_value = await self.db.get(PropertyValue, value_data.value_uid)
                if existing_value:
                    raise ValueError(f"Value UID '{value_data.value_uid}' already exists")
                value = PropertyValue(
                    uid=value_data.value_uid,
                    value=value_data.value,
                    property_uid=property_data.uid
                )
                self.db.add(value)

        await self.db.commit()

        result = await self.db.execute(
            select(Property).options(joinedload(Property.values)).where(Property.uid == property_data.uid)
        )
        property = result.scalars().first()
        return property

    async def delete(self, property_uid: str) -> None:
        property = await self.db.get(Property, property_uid)
        if not property:
            raise ValueError(f"Property with UID '{property_uid}' not found")
        await self.db.execute(delete(Property).where(Property.uid == property_uid))
        await self.db.commit()