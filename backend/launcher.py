"""Entrada do sidecar; seleção explícita do extrator sem carregar o servidor inteiro."""
import sys
if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--extract':
        sys.argv.pop(1)
        from app.extract_material import main
    else:
        from app.__main__ import main
    main()
