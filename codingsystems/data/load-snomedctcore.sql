-- create a temp table to hold everything
create temp table snomedct_core_complete (
       snomed_cid 			 varchar(50),
       snomed_fsn			 varchar(200),
       snomed_concept_status		 varchar(20),
       umls_cui				 varchar(50),
       occurrence			 varchar(20),
       usage				 varchar(20),
       first_in_subset			 varchar(20),
       is_retired_from_subset		 varchar(20),
       last_in_subset			 varchar(50),
       replaced_by_snomed_cid		 varchar(50)
);

-- copy into the temp table
copy snomedct_core_complete from '/home/jmandel/Desktop/smart/smart_server/codingsystems/data/complete/SNOMEDCT_CORE_SUBSET_201005.utf8.txt' with delimiter '|';


-- insert the coding system
insert into codingsystems_codingsystem
(short_name, description)
select 'umls-snomed', 'UMLS concept codes for SNOMED core'
where not exists (select 1 from codingsystems_codingsystem where short_name = 'umls-snomed');

-- select the fields we need and insert into coded values
insert into codingsystems_codedvalue
(code, system_id, umls_code, full_value)
select
snomed_cid, codingsystems_codingsystem.id, umls_cui, snomed_fsn from snomedct_core_complete, codingsystems_codingsystem
where short_name = 'umls-snomed';

