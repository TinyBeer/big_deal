let obj = text("箭头小画家").findOne(100).parent().parent().parent();
console.log(obj.child(2).child(0));

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
