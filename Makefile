format:
	ruff format . & ruff check --fix .

shell:
	python src/shell.py

migrate-reset-latest:
	aerich downgrade
	@latest_migration=$$(ls -t src/migrations/core/*.py | grep -v __init__.py | head -1) && \
	if [ -n "$$latest_migration" ]; then \
		echo "Deleting: $$latest_migration"; \
		rm "$$latest_migration"; \
	else \
		echo "No migration files found to delete"; \
	fi
	aerich migrate
	aerich upgrade

dbdump:
	@if [ -z "$(DB_NAME)" ]; then \
	  echo "DB_NAME is required"; \
	  exit 1; \
	fi; \
	if [ -z "$(PREFIX)" ] && [ -z "$(SUFFIX)" ]; then \
	  echo "At least one of PREFIX or SUFFIX must be provided"; \
	  exit 1; \
	fi; \
	\
	ENV_OVERRIDES=$$(jq -nc \
	  --arg db "$(DB_NAME)" \
	  '{ \
	    containerOverrides: [{ \
	      name: "pg-dump-task", \
	      environment: [ \
	        {name: "DB_NAME", value: $$db} \
	      ] \
	    }] \
	  }'); \
	\
	if [ -n "$(PREFIX)" ]; then \
	  ENV_OVERRIDES=$$(echo $$ENV_OVERRIDES | jq --arg prefix "$(PREFIX)" \
	    '(.containerOverrides[0].environment) += [{"name":"PREFIX","value":$$prefix}]'); \
	fi; \
	if [ -n "$(SUFFIX)" ]; then \
	  ENV_OVERRIDES=$$(echo $$ENV_OVERRIDES | jq --arg suffix "$(SUFFIX)" \
	    '(.containerOverrides[0].environment) += [{"name":"SUFFIX","value":$$suffix}]'); \
	fi; \
	if [ -n "$(EXCLUDE)" ]; then \
	  ENV_OVERRIDES=$$(echo $$ENV_OVERRIDES | jq --arg exclude "$(EXCLUDE)" \
	    '(.containerOverrides[0].environment) += [{"name":"EXCLUDE","value":$$exclude}]'); \
	fi; \
	\
	echo "Starting ECS task with overrides"; \
	aws ecs run-task \
	  --cluster ba-cluster \
	  --launch-type EC2 \
	  --task-definition pg-dump-task \
	  --overrides "$$ENV_OVERRIDES" \
	  --count 1 \
	  > /dev/null 2>&1; \
	\
	echo "ECS task started. Monitor discord for when the task finishes";


download_dump:
	@if [ -z "$(DB_NAME)" ]; then echo "DB_NAME is required"; exit 1; fi; \
	if [ -z "$(FILE)" ]; then echo "FILE is required"; exit 1; fi; \
	aws s3 cp "s3://pg-dumps-ftw/$(DB_NAME)/$(FILE)" .


NUMPROC := $(shell \
    if command -v nproc > /dev/null; then \
        nproc; \
    elif command -v sysctl > /dev/null; then \
        sysctl -n hw.ncpu; \
    else \
        echo 4; \
    fi)


dbrestore:
	@if [ -z "$(FILE)" ]; then echo "FILE is required"; exit 1; fi; \
	PGPASSWORD=postgres pg_restore -v -j $(NUMPROC) \
	-U blockanalitica \
	-h 127.0.0.1 \
	-p 5476 \
	-d sky \
	"$(FILE)"

list-api:
	aws ecs list-tasks --cluster ba-cluster --family atlas-axis

ecs-exec:
	@task_id=$$(aws ecs list-tasks \
		--cluster ba-cluster \
		--family atlas-axis \
		--desired-status RUNNING \
		--output text \
		--query 'taskArns[0]' | awk -F/ '{print $$NF}'); \
	aws ecs execute-command \
		--region eu-west-1 \
		--cluster ba-cluster \
		--task $$task_id \
		--command "bash" \
		--interactive
