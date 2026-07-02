const Parser = require('tree-sitter');
const fs = require('fs');

// Basic parser without language (will show structure anyway)
const parser = new Parser();

const sourceCode = fs.readFileSync('./neurocommander.sh', 'utf8');
const tree = parser.parse(sourceCode);

console.log('NeuroCommander Code Structure:');
console.log('Tree type:', tree.rootNode.type);
console.log('Children count:', tree.rootNode.children.length);

function printNode(node, depth = 0) {
    if (depth > 3) return; // Limit depth
    
    const indent = '  '.repeat(depth);
    console.log(`${indent}${node.type}: "${node.text.slice(0, 50)}${node.text.length > 50 ? '...' : ''}"`);
    
    for (const child of node.children) {
        printNode(child, depth + 1);
    }
}

console.log('\nFirst few nodes:');
printNode(tree.rootNode, 0);