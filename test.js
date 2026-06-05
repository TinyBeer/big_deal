let obj = text("养猪猪").findOne(100).parent().parent().parent();
displayArchitecture(obj, 1)

function displayArchitecture_Name(name) {
  let root = text(name).findOne(100);
  console.log(root);
  
  if (root == null) {
    return;
  }

  displayArchitecture(root, 1);
}

function displayArchitecture(root, depth) {
  console.log("->".repeat(depth),"id:", root.id(), "text:", root.text(), "desc:", root.desc(), "ccount:", root.childCount(), "bounds:", root.bounds());
  for (let idx = 0; idx < root.children().length; idx++) {
    let child = root.children()[idx];
    displayArchitecture(child, depth + 1);
  }
}
