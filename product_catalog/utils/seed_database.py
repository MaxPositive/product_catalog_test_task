import asyncio
import os
import json
from product_catalog.domain.models import Product, Property, PropertyValue, ProductProperty, PropertyType
from product_catalog.di.database import get_engine, get_session_maker


async def seed_database(json_file_path: str):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    engine = await get_engine()
    session_maker = await get_session_maker(engine)

    async with session_maker() as session:
        property_map = {}
        for prop_data in data["properties"]:
            existing_prop = await session.get(Property, prop_data["uid"])
            if not existing_prop:
                prop = Property(
                    uid=prop_data["uid"],
                    name=prop_data["name"],
                    type=PropertyType[prop_data["type"].upper()]
                )
                session.add(prop)
                property_map[prop.uid] = prop_data["type"]

                if prop_data["type"] == "list":
                    for value_data in prop_data["values"]:
                        existing_value = await session.get(PropertyValue, value_data["uid"])
                        if not existing_value:
                            value = PropertyValue(
                                uid=value_data["uid"],
                                value=value_data["value"],
                                property_uid=prop_data["uid"]
                            )
                            session.add(value)

        for product_data in data["products"]:
            existing_product = await session.get(Product, product_data["uid"])
            if not existing_product:
                product = Product(
                    uid=product_data["uid"],
                    name=product_data["name"]
                )
                session.add(product)

                for prop_data in product_data["properties"]:
                    prop_type = property_map.get(prop_data["uid"])
                    if prop_type == "list":
                        product_property = ProductProperty(
                            product_uid=product_data["uid"],
                            property_uid=prop_data["uid"],
                            value_uid=prop_data["value_uid"]
                        )
                    elif prop_type == "int":
                        product_property = ProductProperty(
                            product_uid=product_data["uid"],
                            property_uid=prop_data["uid"],
                            int_value=prop_data["value"]
                        )
                    session.add(product_property)

        await session.commit()


async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "vacancy.json")
    await seed_database(json_file_path)

if __name__ == "__main__":
    asyncio.run(main())