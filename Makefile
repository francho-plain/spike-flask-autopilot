SHELL := /bin/bash

.PHONY: copilot-sync

copilot-sync:
	bash .devcontainer/sync-copilot-upstream.sh