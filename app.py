from service import app
import sys


if __name__ == '__main__':
    port = 5005
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    app.run(host='0.0.0.0',port = port, debug=False)
