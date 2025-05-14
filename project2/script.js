const folderStructure = [
  {
    name: "Applications and Games",
    files: ["game.exe", "app.zip"]
  },
  {
    name: "Compressed Files",
    files: ["project.rar", "backup.zip"]
  },
  {
    name: "Images",
    files: ["photo1.jpg", "screenshot.png"]
  },
  {
    name: "Install Media",
    files: ["windows.iso", "ubuntu.iso"]
  },
  {
    name: "Musics",
    files: ["song.mp3", "track.wav"]
  },
  {
    name: "Other Files",
    files: ["notes.txt", "data.json"]
  },
  {
    name: "Text Files",
    files: ["doc1.txt", "summary.md"]
  },
  {
    name: "Web Files",
    files: ["index.html", "style.css", "script.js"]
  },
  {
    name: "desktop.ini",
    files: []
  }
];

const folderList = document.getElementById("folder-list");

folderStructure.forEach((folder, index) => {
  const folderItem = document.createElement("li");
  folderItem.className = "folder-item";
  folderItem.id = `folder-${index}`;
  folderItem.innerHTML = `📁 ${folder.name}`;

  const fileSublist = document.createElement("ul");
  fileSublist.className = "file-sublist";
  fileSublist.id = `files-${index}`;

  folder.files.forEach((file, i) => {
    const fileItem = document.createElement("li");
    fileItem.className = "file-item";
    fileItem.id = `file-${index}-${i}`;
    fileItem.textContent = `📄 ${file}`;
    fileSublist.appendChild(fileItem);
  });

  folderItem.addEventListener("click", () => {
    fileSublist.style.display =
      fileSublist.style.display === "none" ? "block" : "none";
  });

  folderList.appendChild(folderItem);
  if (folder.files.length > 0) {
    folderList.appendChild(fileSublist);
  }
});
