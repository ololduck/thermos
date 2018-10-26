#!/usr/bin/fish
pipenv install --dev
pipenv run ansible-playbook $argv