# Makefile for Blockchain Project (Please refer video if not execution instructions not clear)

# Targets
all: blockchain_server server metronome_server pool_server test validator

blockchain_server:
	python blockchain_server.py

server:
  python server.py

metronome_server:
	python metronome_server.py

pool_server:
	python pool_server.py

test:
  test.py

validator:
	python validator.py

