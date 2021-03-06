import argparse
import functools

from pyspark.sql import SparkSession
from pyspark.sql.types import (
	StructType, StringType, StructField
)
from pyspark.sql.functions import lit, col

contact_schema = StructType([
	StructField("identifier", StringType()),
	StructField("name", StringType()),
	StructField("address_1", StringType()),
	StructField("address_2", StringType()),
	StructField("address_3", StringType()),
	StructField("address_4", StringType()),
	StructField("city", StringType()),
	StructField("state_province", StringType()),
	StructField("zip_code", StringType()),
	StructField("country_code", StringType()),
	StructField("contact_name", StringType()),
	StructField("comm_number_qualifier", StringType()),
	StructField("comm_number", StringType())
])
contacts = ['consignee', 'notifyparty', 'shipper']

def create_spark_session():
	spark = SparkSession \
		.builder \
		.getOrCreate()

	return spark

def get_contact_dataframe(spark, name, input_dir):
	"""
	Get a contact dataframe
	
	Parameters
	----------
	spark : Spark session
		Current Spark session
	name : str
		Name of the dataset
	input_dir : str
		Input directory

	Returns
	-------
	Spark dataset
		The contact dataset
	"""
	df = spark.read \
		.option("header", True) \
		.option("escape", '"') \
		.option("enforceSchema", True) \
		.option("schema", contact_schema) \
		.csv(f"{input_dir}/ams/*/*/ams__{name}_*__*.csv") \
		.where(col('identifier').isNotNull())

	return df.withColumn('contact_type', lit(name))

def process_contact_data(spark, input_dir, ouput):
	"""
	Process contact data by concatenating the contact dataframes 
	
	Parameters
	----------
	spark : Spark session
		Current Spark session
	input_dir : str
		Input directory
	output : str
		Input directory
	"""
	contact_dfs = list(map(
		lambda name: get_contact_dataframe(spark, name, input_dir), 
		contacts
	))
	contact_df = functools.reduce(lambda a,b: a.union(b), contact_dfs)

	contact_df.repartition(1).write.mode('overwrite').format("csv") \
		.option("header", True) \
		.option("escape", '"') \
		.save(f"{ouput}/contact/")

def main(input_dir, output):
	"""
	Process contact data by concatenating the contact dataframes 
	
	Parameters
	----------
	input_dir : str
		Input directory
	output : str
		Input directory
	"""
	spark = create_spark_session()
	process_contact_data(spark, input_dir, output)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', default='/input')
	parser.add_argument('-o', '--output', default='/output')
	args = parser.parse_args()

	main(args.input, args.output)
