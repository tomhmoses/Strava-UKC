import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div className='px-4 pt-2'>
        <h1 className='text-2xl font-bold pb-1'>Vite + React + Tailwind</h1>
        <div>
          <button onClick={() => setCount((count) => count + 1)}  className="text-l font-bold underline backdrop-blur p-3 text-white bg-gray-800 hover:bg-orange-400">
            count is {count}
          </button>
        </div>
      </div>
    </>
  )
}

export default App
