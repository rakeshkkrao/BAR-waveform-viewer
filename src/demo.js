uki([
    {view:'ScrollableList', rect:'0 100 300 100', anchors:'left top bottom', 
     id: 'source', textSelectable: false, multiselect: true, draggable: true},
     { view: 'Label', rect: '300 100 600 100', anchors: 'left top', text: 'drop target',
	style: { fontSize: '25px', textAlign: 'center' },
	background: 'cssBox(border:2px dashed #CCC; background:#EEE)', name: 'target' }
]).attachTo(window);

var data = [1,2,3,4,5,6];

uki('#source List')
	.data(data)
	.dragstart(function(e) {
		e.dataTransfer.setData('text/plain',this.selectedRows().join('\n'));
		e.dataTransfer.setDragImage(uki(
        		{view: 'Label', rect: '100 20', anchors: 'left top', inset: '0 5',
          		background: 'cssBox(border: 1px solid #CCC;background:#EEF)',
          		text: this.selectedRows().length + ' rows' }
     			), 10, 10);		
		e.dataTransfer.effectAllowed = 'copy';
	});


uki('[name=target]')
	.dragover(function(e) {
	e.preventDefault();
	e.dataTransfer.dropEffect = 'copy';
  })
	.dragenter(function(e) {
	this.text('over');
  })
	.dragleave(function(e) {
	this.text('drop target');
  })
	 .drop(function(e) {
	e.preventDefault();
	this.text('droped');
	alert(e.dataTransfer.getData('text/plain'))
	
  });
