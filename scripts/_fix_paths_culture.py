import io, json, os, glob

root = r"C:\Users\capatino\Documents\Inasistencias Sofía Plus"
old_root = r"C:\Users\capatino\Documents\Caracterización de aprendices\Dashboard_Aprendices_SENA\Caracterizacion_Aprendices_ASTIN"

# 1) RutaDatos parameter
p = os.path.join(root, "CaracterizacionAprendicesASTIN.SemanticModel", "definition", "expressions.tmdl")
s = io.open(p, encoding="utf-8").read()
s = s.replace(old_root, root)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("updated", p)

# 2) ETL audit source path
p = os.path.join(root, "data", "processed", "00_resumen_etl.json")
d = json.load(io.open(p, encoding="utf-8"))
d["fuente"] = os.path.join(root, "data", "raw", "Inasistencias.xls")
io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(d, ensure_ascii=False, indent=2))
print("updated", p)

# 3) CSV culture for all partitions
old = '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]'
new = '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv, Culture="en-US"]'
for p in glob.glob(os.path.join(root, "CaracterizacionAprendicesASTIN.SemanticModel", "definition", "tables", "*.tmdl")):
    s = io.open(p, encoding="utf-8").read()
    n = s.count(old)
    if n:
        s = s.replace(old, new)
        io.open(p, "w", encoding="utf-8", newline="").write(s)
        print("culture", n, os.path.basename(p))

# 4) generator template
p = os.path.join(root, "scripts", "02_generar_modelo_tmdl.py")
s = io.open(p, encoding="utf-8").read()
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("updated generator culture")

print("done")
