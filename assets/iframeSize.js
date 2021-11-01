const resizeObserver = new ResizeObserver(entries => 
  parent.postMessage({ id: location.port, height: entries[0].target.clientHeight }, "https://bczarnecki.com")
)
resizeObserver.observe(document.body)