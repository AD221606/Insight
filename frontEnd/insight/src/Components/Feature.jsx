import './Feature.css';

export default function Feature({title, desc, handleClickSection}){
    return (
        <section className='feature' onClick={() => handleClickSection(title)}>
            <h3>{title}</h3>
            <p>{desc}</p>
        </section>
    );
}