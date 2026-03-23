const major = Number.parseInt(process.versions.node.split(".")[0] ?? "", 10);

const minimumMajor = 22;
const maximumMajor = 24;

if (Number.isNaN(major)) {
  console.error("Nao foi possivel detectar a versao do Node.js.");
  process.exit(1);
}

if (major < minimumMajor || major > maximumMajor) {
  console.error(
    [
      "",
      `Este projeto precisa de um runtime Node.js LTS entre ${minimumMajor} e ${maximumMajor}.`,
      `Versao detectada: ${process.versions.node}.`,
      "",
      "Motivo:",
      "- o app web em Next.js esta entrando em estado de inicializacao sem abrir a porta local neste runtime;",
      "- para este projeto, padronizamos Node 22 LTS para desenvolvimento local.",
      "",
      "Como seguir:",
      "- use Node 22 LTS;",
      "- depois rode `npm install` na raiz do repositorio;",
      "- por fim rode `npm run dev:web`.",
      "",
    ].join("\n"),
  );

  process.exit(1);
}
